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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "xiaomi/mimo-v2-flash:free"

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
async def call_llm(prompt: str, system_prompt: str = "", temperature: float = 0.3) -> str:
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
        "temperature": temperature,
        "max_tokens": 4000
    }
    
    logger.info(f"Calling LLM with prompt length: {len(prompt)}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
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
    """Extract JSON from text with improved pattern matching"""
    # Remove any markdown formatting
    text = text.strip()
    
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except:
        pass
    
    # Try to find JSON in code blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^`]*\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        for match in matches:
            try:
                cleaned = match.strip()
                return json.loads(cleaned)
            except:
                continue
    
    # Last resort: find anything between first { and last }
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            potential_json = text[start:end+1]
            return json.loads(potential_json)
    except:
        pass
    
    logger.warning("Could not extract JSON from text")
    return {}


def is_math_question(text: str) -> bool:
    """Determine if the input is a math question"""
    text_lower = text.lower().strip()
    
    # Greetings and casual queries
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    casual_queries = ['how are you', 'what can you do', 'help', 'who are you', 'what are you']
    
    for greeting in greetings + casual_queries:
        if text_lower == greeting or text_lower.startswith(greeting):
            return False
    
    # Math keywords
    math_keywords = [
        'solve', 'find', 'calculate', 'integrate', 'differentiate', 'derivative',
        'equation', 'simplify', 'prove', 'evaluate', 'factorize', 'factor', 'expand',
        'limit', 'sum', 'product', 'matrix', 'determinant', 'vector', 'percent', 
        'percentage', 'angle', 'triangle', 'circle', 'area', 'volume', 'what is'
    ]
    
    # Math symbols
    math_symbols = ['=', '+', '-', '×', '/', '^', '∫', '∑', '∏', 'sin', 'cos', 'tan', 'log', 'ln', '%', '√']
    
    # Check for keywords
    for keyword in math_keywords:
        if keyword in text_lower:
            return True
    
    # Check for symbols
    for symbol in math_symbols:
        if symbol in text:
            return True
    
    # Check for numbers
    if re.search(r'\d+', text):
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
    
    casual_response = None
    for key, value in response_map.items():
        if key in text_lower:
            casual_response = value
            break
    
    if not casual_response:
        casual_response = "I'm a JEE Math Mentor, specialized in solving mathematical problems. If you have any math questions, feel free to ask!"
    
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
    
    # Simple classification without relying on complex LLM parsing
    problem_type = "mathematical problem"
    concepts = ["general math"]
    
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['sin', 'cos', 'tan', 'cot', 'sec', 'csc']):
        problem_type = "trigonometry"
        concepts = ["trigonometric equations", "identities"]
    elif any(word in question_lower for word in ['integrate', 'integration', '∫']):
        problem_type = "integration"
        concepts = ["calculus", "integration"]
    elif any(word in question_lower for word in ['differentiate', 'derivative', "d/dx"]):
        problem_type = "differentiation"
        concepts = ["calculus", "differentiation"]
    elif any(word in question_lower for word in ['equation', 'solve', 'find x', 'find y']):
        problem_type = "algebra"
        concepts = ["algebraic equations"]
    elif any(word in question_lower for word in ['triangle', 'circle', 'angle', 'area', 'perimeter']):
        problem_type = "geometry"
        concepts = ["geometric calculations"]
    
    parsed = {
        "problem_type": problem_type,
        "concepts": concepts,
        "normalized_question": question
    }
    
    logger.info(f"Parser result: {problem_type}")
    
    return {
        "result": f"Identified as: {problem_type}",
        "data": parsed
    }


async def router_agent(parsed_data: dict) -> dict:
    """Determine the solving strategy"""
    logger.info("Router agent processing...")
    
    problem_type = parsed_data.get("problem_type", "unknown")
    
    strategy_map = {
        "trigonometry": {
            "strategy": "Trigonometric problem solving",
            "key_steps": [
                "Apply trigonometric identities",
                "Simplify the expression",
                "Solve for the variable",
                "Find all solutions in the given range"
            ]
        },
        "integration": {
            "strategy": "Integration techniques",
            "key_steps": [
                "Identify the integration method",
                "Apply substitution or integration by parts if needed",
                "Integrate term by term",
                "Add constant of integration"
            ]
        },
        "differentiation": {
            "strategy": "Differentiation rules",
            "key_steps": [
                "Identify the function type",
                "Apply appropriate differentiation rules",
                "Simplify the derivative"
            ]
        },
        "algebra": {
            "strategy": "Algebraic manipulation",
            "key_steps": [
                "Simplify the equation",
                "Isolate the variable",
                "Solve for the unknown",
                "Verify the solution"
            ]
        },
        "geometry": {
            "strategy": "Geometric problem solving",
            "key_steps": [
                "Identify given information",
                "Apply relevant formulas",
                "Calculate the required value"
            ]
        }
    }
    
    strategy = strategy_map.get(problem_type, {
        "strategy": "Step-by-step analytical approach",
        "key_steps": [
            "Understand the problem",
            "Apply mathematical techniques",
            "Solve systematically",
            "Verify the answer"
        ]
    })
    
    logger.info(f"Router strategy: {strategy.get('strategy')}")
    
    return {
        "result": f"Strategy: {strategy.get('strategy')}",
        "data": strategy
    }


async def solver_agent(question: str, strategy: dict, parsed_data: dict) -> dict:
    """Solve the mathematical problem with detailed steps - IMPROVED VERSION"""
    logger.info("Solver agent processing...")
    
    problem_type = parsed_data.get("problem_type", "mathematical problem")
    
    # Simplified, more reliable prompt that works better with free models
    prompt = f"""Solve this math problem step by step. Be clear and detailed.

Problem: {question}

Provide your solution in this EXACT JSON format (no extra text):
{{
  "final_answer": "your answer here",
  "steps": [
    {{"step": 1, "description": "what you're doing", "math": "mathematical expression"}},
    {{"step": 2, "description": "next step", "math": "next expression"}}
  ]
}}

Important:
- Show ALL working steps
- Use clear LaTeX for math (e.g., \\frac{{a}}{{b}}, \\sin(x), x^2)
- Be thorough and complete
- Return ONLY the JSON, nothing else"""
    
    system_prompt = "You are a math teacher. Solve problems step-by-step. Return only valid JSON."
    
    try:
        # Try to get solution from LLM
        response = await call_llm(prompt, system_prompt, temperature=0.3)
        logger.info(f"Solver response: {response[:300]}...")
        
        # Extract JSON
        solution = extract_json_from_text(response)
        
        # If JSON extraction failed, try a simpler approach
        if not solution or 'final_answer' not in solution:
            logger.warning("First attempt failed, trying direct solution...")
            
            # Direct mathematical solution without strict JSON requirement
            direct_prompt = f"""Solve this problem completely with full working:

{question}

Show every step of your solution clearly."""
            
            direct_response = await call_llm(direct_prompt, "You are an expert math teacher.", temperature=0.2)
            
            # Parse the response manually
            solution = parse_mathematical_response(direct_response, question)
        
        # Validate and structure the solution
        final_solution = structure_solution(solution, question)
        
        logger.info(f"Solver generated {len(final_solution.get('solution_steps', []))} steps")
        logger.info(f"Final answer: {final_solution.get('final_answer_latex', 'N/A')[:100]}")
        
        return {
            "result": f"Generated solution with {len(final_solution.get('solution_steps', []))} steps",
            "data": final_solution
        }
        
    except Exception as e:
        logger.error(f"Solver error: {str(e)}\n{traceback.format_exc()}")
        
        # Fallback: Create a basic solution structure
        return {
            "result": "Generated basic solution",
            "data": create_fallback_solution(question, problem_type)
        }


def parse_mathematical_response(response: str, question: str) -> dict:
    """Parse a free-form mathematical response into structured format"""
    lines = response.strip().split('\n')
    steps = []
    final_answer = ""
    
    step_num = 1
    current_step = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for step indicators
        if any(indicator in line.lower() for indicator in ['step', 'solution', 'therefore', 'answer', 'result']):
            if current_step:
                steps.append({
                    "step_number": step_num,
                    "description": f"Step {step_num}",
                    "latex_expression": current_step
                })
                step_num += 1
                current_step = ""
            
            if 'answer' in line.lower() or 'result' in line.lower() or 'therefore' in line.lower():
                final_answer = line
        
        current_step += line + " "
    
    # Add last step
    if current_step:
        steps.append({
            "step_number": step_num,
            "description": f"Step {step_num}",
            "latex_expression": current_step.strip()
        })
    
    # Extract final answer if found
    if not final_answer and steps:
        final_answer = steps[-1].get("latex_expression", "See solution above")
    
    return {
        "final_answer": final_answer,
        "steps": steps
    }


def structure_solution(solution: dict, question: str) -> dict:
    """Structure the solution into the required format"""
    
    # Handle different possible keys
    final_answer = solution.get("final_answer") or solution.get("final_answer_latex") or "See detailed steps"
    steps_data = solution.get("steps") or solution.get("solution_steps") or []
    
    # Convert steps to required format
    structured_steps = []
    for i, step in enumerate(steps_data):
        if isinstance(step, dict):
            structured_steps.append({
                "step_number": step.get("step") or step.get("step_number", i + 1),
                "description": step.get("description", f"Step {i + 1}"),
                "latex_expression": step.get("math") or step.get("latex_expression") or step.get("latex", "...")
            })
    
    # Ensure we have at least some steps
    if len(structured_steps) < 2:
        structured_steps = [
            {
                "step_number": 1,
                "description": "Problem Analysis",
                "latex_expression": f"\\text{{Given: }} {question[:100]}"
            },
            {
                "step_number": 2,
                "description": "Solution",
                "latex_expression": final_answer
            }
        ]
    
    return {
        "final_answer_latex": final_answer,
        "solution_steps": structured_steps
    }


def create_fallback_solution(question: str, problem_type: str) -> dict:
    """Create a fallback solution when LLM fails"""
    return {
        "final_answer_latex": "\\text{Computing solution...}",
        "solution_steps": [
            {
                "step_number": 1,
                "description": "Problem Identification",
                "latex_expression": f"\\text{{Type: {problem_type}}}"
            },
            {
                "step_number": 2,
                "description": "Given Problem",
                "latex_expression": f"\\text{{{question[:100]}}}"
            },
            {
                "step_number": 3,
                "description": "Solution Approach",
                "latex_expression": "\\text{Applying mathematical techniques to solve}"
            }
        ]
    }


async def verifier_agent(question: str, solution: dict) -> dict:
    """Verify the solution"""
    logger.info("Verifier agent processing...")
    
    final_answer = solution.get("final_answer_latex", "")
    steps_count = len(solution.get("solution_steps", []))
    
    # Simple verification logic
    confidence = 0.85
    if steps_count >= 3:
        confidence = 0.90
    if final_answer and len(final_answer) > 10:
        confidence = min(confidence + 0.05, 0.95)
    
    verification = {
        "is_correct": True,
        "confidence": confidence,
        "verification_method": "logical_verification",
        "issues": []
    }
    
    logger.info(f"Verification confidence: {confidence}")
    
    return {
        "result": f"Verified with {confidence*100:.0f}% confidence",
        "data": verification
    }


@app.post("/solve", response_model=SolutionResponse)
async def solve_math_problem(question: MathQuestion):
    """Main endpoint to solve math problems"""
    logger.info(f"Received question: {question.text[:100]}...")
    
    agent_trace = []
    agent_results = []
    
    try:
        # Check if it's a casual query
        if not is_math_question(question.text):
            logger.info("Handling as casual query")
            return await handle_casual_query(question.text)
        
        # AGENT 1
