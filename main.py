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
    """
    Determine if the input is a math question.
    Returns True for math questions, False for casual greetings/chat.
    """
    text_lower = text.lower().strip()
    
    # Define exact match greetings (very short, no math context)
    pure_greetings = [
        'hi', 'hello', 'hey', 'hi there', 'hello there',
        'good morning', 'good afternoon', 'good evening',
        'how are you', 'how are you?', 'whats up', "what's up",
        'sup', 'yo'
    ]
    
    # Check for exact greeting matches (entire message is just a greeting)
    if text_lower in pure_greetings:
        logger.info(f"Detected pure greeting: {text_lower}")
        return False
    
    # Define casual query patterns
    casual_patterns = [
        r'^what can you do\??$',
        r'^who are you\??$',
        r'^what are you\??$',
        r'^help me$',
        r'^help\??$',
        r'^introduce yourself$'
    ]
    
    for pattern in casual_patterns:
        if re.match(pattern, text_lower):
            logger.info(f"Detected casual query: {text_lower}")
            return False
    
    # Math keywords - expanded list
    math_keywords = [
        'solve', 'find', 'calculate', 'compute', 'integrate', 'differentiate', 
        'derivative', 'equation', 'simplify', 'prove', 'evaluate', 'factorize', 
        'factor', 'expand', 'limit', 'sum', 'product', 'matrix', 'determinant', 
        'vector', 'percent', 'percentage', 'what is', 'how much', 'how many',
        'value of', 'result of', 'answer to', 'solution to', 'squared', 'cubed',
        'root', 'sqrt', 'power', 'exponent', 'logarithm', 'tangent', 'sine',
        'cosine', 'angle', 'area', 'volume', 'perimeter', 'distance', 'speed',
        'rate', 'ratio', 'proportion', 'probability', 'permutation', 'combination',
        'median', 'mean', 'mode', 'standard deviation', 'variance'
    ]
    
    # Check for math keywords
    for keyword in math_keywords:
        if keyword in text_lower:
            logger.info(f"Detected math keyword: {keyword}")
            return True
    
    # Math symbols and patterns - expanded
    math_symbols = [
        '=', '+', '-', '×', '÷', '*', '/', '^', '√', '∫', '∑', '∏', 
        '∂', 'π', '°', '≤', '≥', '≠', '≈', '∞', '%'
    ]
    
    for symbol in math_symbols:
        if symbol in text:
            logger.info(f"Detected math symbol: {symbol}")
            return True
    
    # Math function patterns
    math_functions = [
        r'\bsin\b', r'\bcos\b', r'\btan\b', r'\blog\b', r'\bln\b',
        r'\bexp\b', r'\babs\b', r'\bmax\b', r'\bmin\b', r'\bsec\b',
        r'\bcsc\b', r'\bcot\b', r'\bsinh\b', r'\bcosh\b', r'\btanh\b'
    ]
    
    for func_pattern in math_functions:
        if re.search(func_pattern, text_lower):
            logger.info(f"Detected math function: {func_pattern}")
            return True
    
    # Number patterns indicating math
    number_patterns = [
        r'\d+\s*[\+\-\*/\^×÷]\s*\d+',  # Basic arithmetic: 5 + 3
        r'\d+\s*=\s*\d+',  # Equations: x = 5
        r'\d+\s*[<>≤≥]\s*\d+',  # Inequalities
        r'\d+\.\d+',  # Decimals: 3.14
        r'\d+/\d+',  # Fractions: 3/4
        r'\d+\^',  # Exponents: 2^3
        r'\d+%',  # Percentages: 50%
        r'x\s*[\+\-\*/\^=]',  # Variable operations
        r'[a-z]\s*=\s*\d+',  # Variable assignments: x = 5
    ]
    
    for pattern in number_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"Detected math number pattern: {pattern}")
            return True
    
    # Question patterns that suggest math
    math_question_patterns = [
        r'what is \d+',  # "what is 5 + 3"
        r'how much is',
        r'how many',
        r'calculate',
        r'find the (value|answer|solution|result)',
    ]
    
    for pattern in math_question_patterns:
        if re.search(pattern, text_lower):
            logger.info(f"Detected math question pattern: {pattern}")
            return True
    
    # If we have numbers AND it's a question, likely math
    has_numbers = bool(re.search(r'\d+', text))
    is_question = '?' in text or any(text_lower.startswith(q) for q in ['what', 'how', 'find', 'solve', 'calculate'])
    
    if has_numbers and is_question:
        logger.info("Detected numbers + question format = math")
        return True
    
    # Default: if it contains any numbers, treat as potential math
    # (better to solve a math question than reject it)
    if has_numbers:
        logger.info("Contains numbers, treating as math question")
        return True
    
    logger.info(f"No math indicators found, treating as casual: {text_lower}")
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
1. problem_type (e.g., "trigonometry", "integration", "differentiation", "algebra", "geometry", "arithmetic", "calculus")
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
        },
        "arithmetic": {
            "strategy": "Arithmetic computation",
            "key_steps": [
                "Identify the operations needed",
                "Perform calculations step by step",
                "Verify the final answer"
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
    
    prompt = f"""You are an expert JEE mathematics teacher and professional problem solver who solves ANY mathematical problem. Use KaTeX for all formulas.

Question: {question}

Problem Type: {problem_type}
Approach: {strategy.get('strategy', 'analytical approach')}

IMPORTANT INSTRUCTIONS:
1. Provide a COMPLETE solution with ALL steps shown
2. Each step should show actual mathematical work, not just descriptions
3. Use proper LaTeX formatting for all mathematical expressions
4. Show intermediate calculations clearly
5. The final answer should be exact and complete
6. Solve ANY type of math problem - arithmetic, algebra, calculus, geometry, etc.

Return your response as valid JSON in this EXACT format:
{{
  "final_answer_latex": "complete final answer in LaTeX (e.g., x = \\\\frac{{\\\\pi}}{{6}}, \\\\frac{{5\\\\pi}}{{6}} or 42 or \\\\frac{{15}}{{4}})",
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
- For arithmetic, show each calculation step
- Include at least 3-6 detailed steps
- ALWAYS provide a numerical or symbolic final answer

Return ONLY the JSON, nothing else."""
    
    system_prompt = """You are an expert JEE mathematics teacher and professional problem solver who solves ANY problem presented.
Never skip steps. Show all mathematical work. Use proper LaTeX formatting.
Return only valid JSON with complete solutions. You can solve arithmetic, algebra, calculus, geometry, and all types of math problems."""
    
    try:
        response = await call_llm(prompt, system_prompt)
        logger.info(f"Solver raw response length: {len(response)}")
        
        solution = extract_json_from_text(response)
        
        # Validate and fix solution structure
        if not solution or 'final_answer_latex' not in solution:
            logger.warning("Solver response missing final_answer_latex, creating default")
            solution = {
                "final_answer_latex": "\\text{Solution computed}",
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
            "result": f"Generated detailed solution with {len(solution.get('soluti
