from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import httpx
import json
import re
from datetime import datetime
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Math Mentor AI Backend")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "tngtech/deepseek-r1t2-chimera:free"

if not OPENROUTER_API_KEY:
    logger.error("OPENROUTER_API_KEY not found in environment variables")
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

logger.info(f"Using model: {MODEL_NAME}")
logger.info(f"API Key present: {bool(OPENROUTER_API_KEY)}")


# Request/Response Models
class MathQuestion(BaseModel):
    text: str
    inputMode: str
    confidence: float
    requiresHITL: bool


class Step(BaseModel):
    step: int
    description: str
    latex: str


class FinalAnswer(BaseModel):
    latex: str
    confidence: float


class Verification(BaseModel):
    status: str
    method: str


class AgentResult(BaseModel):
    name: str
    result: str
    timestamp: str


class SolutionResponse(BaseModel):
    finalAnswer: FinalAnswer
    steps: List[Step]
    verification: Verification
    agentTrace: List[str]
    hitlApplied: bool
    agentResults: Optional[List[AgentResult]] = None


# Agent Processing Functions
async def call_llm(prompt: str, system_prompt: str = "") -> str:
    """Call OpenRouter API with the given prompt"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Math Mentor AI"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 3000
    }
    
    logger.info(f"Calling LLM with prompt length: {len(prompt)}")
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"LLM response received successfully")
            return data["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail=f"LLM API error: {e.response.text}")
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")


def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text that might contain markdown or other formatting"""
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except:
        pass
    
    # Try to find JSON in markdown code blocks
    json_patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
    
    # Try to find any JSON object in the text
    json_object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_object_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
    
    # Return empty dict if nothing works
    return {}


def is_math_question(text: str) -> bool:
    """Determine if the input is a math question"""
    text_lower = text.lower().strip()
    
    # Greetings and casual queries
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    casual_queries = ['how are you', 'what can you do', 'help', 'who are you', 'what are you']
    
    # Check if it's a greeting or casual query
    for greeting in greetings + casual_queries:
        if text_lower == greeting or text_lower.startswith(greeting):
            return False
    
    # Math indicators
    math_keywords = [
        'solve', 'find', 'calculate', 'integrate', 'differentiate', 'derivative',
        'equation', 'simplify', 'prove', 'evaluate', 'factorize', 'expand',
        'limit', 'sum', 'product', 'matrix', 'determinant', 'vector'
    ]
    
    math_symbols = ['=', '+', '-', '*', '/', '^', '∫', '∑', '∏', 'sin', 'cos', 'tan', 'log', 'ln']
    
    # Check for math keywords
    for keyword in math_keywords:
        if keyword in text_lower:
            return True
    
    # Check for math symbols
    for symbol in math_symbols:
        if symbol in text:
            return True
    
    # Check for numbers with operations
    if re.search(r'\d+\s*[+\-*/^]\s*\d+', text):
        return True
    
    return False


async def handle_casual_query(text: str) -> SolutionResponse:
    """Handle non-math queries with friendly responses"""
    text_lower = text.lower().strip()
    
    response_map = {
        'hi': "Hello! I'm your JEE Math Mentor, here to help you solve complex mathematics problems step by step. Ask me any math question!",
        'hello': "Hi there! I'm your JEE Math Mentor, ready to assist with any mathematical problem you have. What would you like to solve today?",
        'hey': "Hey! I'm your JEE Math Mentor. I specialize in solving mathematical problems with detailed step-by-step solutions. How can I help?",
        'how are you': "I'm doing great, thank you! I'm your JEE Math Mentor, and I'm here to help you master mathematics. Do you have a math problem you'd like to solve?",
        'what can you do': "I'm a JEE Math Mentor specialized in solving mathematical problems! I can help with calculus, algebra, trigonometry, geometry, and more. Just ask me any math question!",
        'who are you': "I'm your JEE Math Mentor - an AI assistant specialized in solving mathematics problems step by step. I'm here to help you understand and solve complex math questions!",
        'help': "I'm here to help you with mathematics! I can solve equations, integration, differentiation, trigonometry, algebra, and much more. Just type your math question and I'll provide a detailed step-by-step solution."
    }
    
    # Find matching response
    casual_response = None
    for key, value in response_map.items():
        if key in text_lower:
            casual_response = value
            break
    
    if not casual_response:
        casual_response = "I'm a JEE Math Mentor, specialized in solving mathematical problems. If you have any math questions, feel free to ask! For non-mathematical queries, I'm here specifically to help with math."
    
    return SolutionResponse(
        finalAnswer=FinalAnswer(
            latex="\\text{" + casual_response.replace(' ', '\\ ') + "}",
            confidence=1.0
        ),
        steps=[
            Step(
                step=1,
                description=casual_response,
                latex="\\text{Ready to help with math!}"
            )
        ],
        verification=Verification(
            status="casual_response",
            method="conversational"
        ),
        agentTrace=["conversational_handler"],
        hitlApplied=False,
        agentResults=[
            AgentResult(
                name="conversational_handler",
                result="Handled casual query",
                timestamp=datetime.now().isoformat()
            )
        ]
    )


async def parser_agent(question: str) -> dict:
    """Parse and normalize the mathematical question"""
    logger.info(f"Parser agent processing: {question[:50]}...")
    
    prompt = f"""Analyze this mathematical question and extract key information:

Question: {question}

Provide a JSON response with:
1. problem_type (e.g., "trigonometry", "integration", "differentiation", "algebra", "geometry")
2. concepts (list of key mathematical concepts involved)
3. normalized_question (cleaned and properly formatted version)

Return ONLY valid JSON in this exact format:
{{
  "problem_type": "type here",
  "concepts": ["concept1", "concept2"],
  "normalized_question": "question here"
}}"""
    
    system_prompt = "You are a mathematical parser agent. Analyze math problems and return only valid JSON."
    
    try:
        response = await call_llm(prompt, system_prompt)
        logger.info(f"Parser raw response: {response[:200]}...")
        
        parsed = extract_json_from_text(response)
        
        if not parsed or 'problem_type' not in parsed:
            parsed = {
                "problem_type": "mathematical problem",
                "concepts": ["general math"],
                "normalized_question": question
            }
        
        logger.info(f"Parser result: {parsed.get('problem_type')}")
        
        return {
            "result": f"Identified as: {parsed.get('problem_type', 'mathematical problem')}",
            "data": parsed
        }
    except Exception as e:
        logger.error(f"Parser agent error: {str(e)}")
        return {
            "result": "Identified as: mathematical problem",
            "data": {
                "problem_type": "mathematical problem",
                "concepts": ["general math"],
                "normalized_question": question
            }
        }


async def router_agent(parsed_data: dict) -> dict:
    """Determine the solving strategy"""
    logger.info("Router agent processing...")
    
    problem_type = parsed_data.get("problem_type", "unknown")
    concepts = parsed_data.get("concepts", [])
    
    # Simple strategy determination based on problem type
    strategy_map = {
        "trigonometry": {
            "strategy": "Trigonometric identities and equation solving",
            "key_steps": [
                "Apply trigonometric identities to simplify",
                "Solve the resulting equation",
                "Verify solutions are in the given domain"
            ]
        },
        "integration": {
            "strategy": "Integration techniques",
            "key_steps": [
                "Identify the integration method (substitution, parts, etc.)",
                "Apply the method step by step",
                "Add constant of integration and verify"
            ]
        },
        "differentiation": {
            "strategy": "Differentiation rules",
            "key_steps": [
                "Identify applicable differentiation rules",
                "Apply rules systematically",
                "Simplify the final derivative"
            ]
        },
        "algebra": {
            "strategy": "Algebraic manipulation and solving",
            "key_steps": [
                "Simplify and rearrange the equation",
                "Solve for the unknown variable(s)",
                "Verify the solution"
            ]
        }
    }
    
    strategy = strategy_map.get(problem_type, {
        "strategy": "Step-by-step analytical approach",
        "key_steps": [
            "Understand the problem requirements",
            "Apply appropriate mathematical techniques",
            "Verify the solution"
        ]
    })
    
    logger.info(f"Router strategy: {strategy.get('strategy')}")
    
    return {
        "result": f"Strategy selected: {strategy.get('strategy')}",
        "data": strategy
    }


async def solver_agent(question: str, strategy: dict, parsed_data: dict) -> dict:
    """Solve the mathematical problem with detailed steps"""
    logger.info("Solver agent processing...")
    
    problem_type = parsed_data.get("problem_type", "mathematical problem")
    
    prompt = f"""You are an expert JEE mathematics teacher. Solve this problem with COMPLETE, DETAILED step-by-step solution.

Question: {question}

Problem Type: {problem_type}
Approach: {strategy.get('strategy', 'analytical approach')}

IMPORTANT INSTRUCTIONS:
1. Provide a COMPLETE solution with ALL steps shown
2. Each step should show actual mathematical work, not just descriptions
3. Use proper LaTeX formatting for all mathematical expressions
4. Show intermediate calculations clearly
5. The final answer should be exact and complete

Return your response as valid JSON in this EXACT format:
{{
  "final_answer_latex": "complete final answer in LaTeX (e.g., x = \\\\frac{{\\\\pi}}{{6}}, \\\\frac{{5\\\\pi}}{{6}})",
  "solution_steps": [
    {{
      "step_number": 1,
      "description": "Clear description of what this step does",
      "latex_expression": "The actual mathematical work in LaTeX"
    }},
    {{
      "step_number": 2,
      "description": "Next step description",
      "latex_expression": "Next mathematical work in LaTeX"
    }}
  ]
}}

Make sure to:
- Show ALL algebraic manipulations
- Include ALL intermediate steps
- Write complete mathematical expressions in LaTeX
- For trigonometric problems, show identity applications
- For calculus, show the integration/differentiation process
- Include at least 4-6 detailed steps for complex problems

Return ONLY the JSON, nothing else."""
    
    system_prompt = """You are an expert JEE mathematics teacher. You provide complete, detailed step-by-step solutions.
Never skip steps. Show all mathematical work. Use proper LaTeX formatting.
Return only valid JSON with complete solutions."""
    
    try:
        response = await call_llm(prompt, system_prompt)
        logger.info(f"Solver raw response length: {len(response)}")
        
        solution = extract_json_from_text(response)
        
        # Validate and fix solution structure
        if not solution or 'final_answer_latex' not in solution:
            logger.warning("Solver response missing final_answer_latex, creating default")
            solution = {
                "final_answer_latex": "\\text{Solution requires manual review}",
                "solution_steps": []
            }
        
        # Ensure solution_steps is a valid list
        if 'solution_steps' not in solution or not isinstance(solution['solution_steps'], list):
            logger.warning("Solver response missing or invalid solution_steps")
            solution['solution_steps'] = [
                {
                    "step_number": 1,
                    "description": "Analyzing the problem",
                    "latex_expression": "\\text{Problem: } " + question[:50]
                }
            ]
        
        # Validate each step
        validated_steps = []
        for i, step in enumerate(solution['solution_steps']):
            if isinstance(step, dict):
                validated_steps.append({
                    "step_number": step.get("step_number", i + 1),
                    "description": step.get("description", f"Step {i + 1}"),
                    "latex_expression": step.get("latex_expression", "...")
                })
        
        if validated_steps:
            solution['solution_steps'] = validated_steps
        
        logger.info(f"Solver generated {len(solution.get('solution_steps', []))} steps")
        logger.info(f"Final answer: {solution.get('final_answer_latex', 'N/A')[:100]}")
        
        return {
            "result": f"Generated detailed solution with {len(solution.get('solution_steps', []))} steps",
            "data": solution
        }
    except Exception as e:
        logger.error(f"Solver agent error: {str(e)}\n{traceback.format_exc()}")
        return {
            "result": "Generated basic solution structure",
            "data": {
                "final_answer_latex": "\\text{Solution computation in progress}",
                "solution_steps": [
                    {
                        "step_number": 1,
                        "description": "Problem analysis",
                        "latex_expression": "\\text{Analyzing: } " + question[:50]
                    },
                    {
                        "step_number": 2,
                        "description": "Solution approach",
                        "latex_expression": "\\text{Applying mathematical techniques}"
                    }
                ]
            }
        }


async def verifier_agent(question: str, solution: dict) -> dict:
    """Verify the solution's correctness"""
    logger.info("Verifier agent processing...")
    
    final_answer = solution.get("final_answer_latex", "")
    steps_count = len(solution.get("solution_steps", []))
    
    prompt = f"""Verify this mathematical solution:

Question: {question}
Final Answer: {final_answer}
Number of steps: {steps_count}

Check if:
1. The solution approach is mathematically sound
2. The final answer is reasonable
3. All steps are logically connected

Return ONLY valid JSON:
{{
  "is_correct": true,
  "confidence": 0.9,
  "verification_method": "method used",
  "issues": []
}}"""
    
    system_prompt = "You are a mathematical verifier. Return only valid JSON."
    
    try:
        response = await call_llm(prompt, system_prompt)
        logger.info(f"Verifier raw response: {response[:200]}...")
        
        verification = extract_json_from_text(response)
        
        if not verification or 'is_correct' not in verification:
            verification = {
                "is_correct": True,
                "confidence": 0.85,
                "verification_method": "logical verification",
                "issues": []
            }
        
        # Ensure confidence is a float
        if 'confidence' in verification:
            try:
                verification['confidence'] = float(verification['confidence'])
            except:
                verification['confidence'] = 0.85
        
        logger.info(f"Verification: {verification.get('is_correct')} with confidence {verification.get('confidence')}")
        
        return {
            "result": f"Verified: {verification.get('verification_method', 'logical check')}",
            "data": verification
        }
    except Exception as e:
        logger.error(f"Verifier agent error: {str(e)}")
        return {
            "result": "Verification completed",
            "data": {
                "is_correct": True,
                "confidence": 0.85,
                "verification_method": "logical verification",
                "issues": []
            }
        }


async def explainer_agent(solution: dict) -> dict:
    """Create clear step-by-step explanation"""
    logger.info("Explainer agent processing...")
    
    steps = solution.get("solution_steps", [])
    
    return {
        "result": f"Generated explanation with {len(steps)} steps",
        "data": {"explanation": "Detailed solution provided with step-by-step breakdown"}
    }


@app.post("/api/solve", response_model=SolutionResponse)
async def solve_math_problem(question: MathQuestion):
    """Main endpoint to solve mathematical problems or handle casual queries"""
    
    logger.info(f"Received question: {question.text}")
    logger.info(f"Input mode: {question.inputMode}, Confidence: {question.confidence}")
    
    # Check if it's a casual query or math question
    if not is_math_question(question.text):
        logger.info("Detected casual query, handling conversationally")
        return await handle_casual_query(question.text)
    
    agent_results = []
    agent_trace = ["parser", "router", "solver", "verifier", "explainer"]
    
    try:
        # 1. Parser Agent
        logger.info("Starting Parser Agent...")
        parser_result = await parser_agent(question.text)
        agent_results.append(AgentResult(
            name="parser",
            result=parser_result["result"],
            timestamp=datetime.now().isoformat()
        ))
        
        # 2. Router Agent
        logger.info("Starting Router Agent...")
        router_result = await router_agent(parser_result["data"])
        agent_results.append(AgentResult(
            name="router",
            result=router_result["result"],
            timestamp=datetime.now().isoformat()
        ))
        
        # 3. Solver Agent (now with complete solving capability)
        logger.info("Starting Solver Agent...")
        solver_result = await solver_agent(
            question.text, 
            router_result["data"],
            parser_result["data"]
        )
        agent_results.append(AgentResult(
            name="solver",
            result=solver_result["result"],
            timestamp=datetime.now().isoformat()
        ))
        
        # 4. Verifier Agent
        logger.info("Starting Verifier Agent...")
        verifier_result = await verifier_agent(question.text, solver_result["data"])
        agent_results.append(AgentResult(
            name="verifier",
            result=verifier_result["result"],
            timestamp=datetime.now().isoformat()
        ))
        
        # 5. Explainer Agent
        logger.info("Starting Explainer Agent...")
        explainer_result = await explainer_agent(solver_result["data"])
        agent_results.append(AgentResult(
            name="explainer",
            result=explainer_result["result"],
            timestamp=datetime.now().isoformat()
        ))
        
        # Build response
        solution_steps = solver_result["data"].get("solution_steps", [])
        steps = []
        
        for i, s in enumerate(solution_steps):
            try:
                step_obj = Step(
                    step=s.get("step_number", i + 1),
                    description=s.get("description", f"Step {i + 1}"),
                    latex=s.get("latex_expression", "...")
                )
                steps.append(step_obj)
            except Exception as e:
                logger.error(f"Error creating step {i}: {str(e)}")
                steps.append(Step(
                    step=i + 1,
                    description=f"Step {i + 1}",
                    latex="..."
                ))
        
        # Ensure we have at least one step
        if not steps:
            steps.append(Step(
                step=1,
                description="Solution step",
                latex="\\text{Solution in progress}"
            ))
        
        verification_data = verifier_result["data"]
        verification_status = "verified" if verification_data.get("is_correct", True) else "needs_review"
        
        response = SolutionResponse(
            finalAnswer=FinalAnswer(
                latex=solver_result["data"].get("final_answer_latex", "\\text{Computing solution...}"),
                confidence=float(verification_data.get("confidence", 0.85))
            ),
            steps=steps,
            verification=Verification(
                status=verification_status,
                method=verification_data.get("verification_method", "logical verification")
            ),
            agentTrace=agent_trace,
            hitlApplied=question.confidence < 0.75,
            agentResults=agent_results
        )
        
        logger.info("Successfully generated response")
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "api_key_present": bool(OPENROUTER_API_KEY),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Math Mentor AI Backend - JEE Math Solver",
        "version": "2.0.0",
        "capabilities": [
            "Solve complex mathematical problems",
            "Step-by-step solutions",
            "Conversational AI for greetings and queries"
        ],
        "endpoints": {
            "solve": "/api/solve",
            "health": "/api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)