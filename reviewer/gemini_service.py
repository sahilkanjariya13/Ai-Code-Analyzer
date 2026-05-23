import time
import re
import google.generativeai as genai
from django.conf import settings
from api_logs.models import APILog

def review_code(code, language, user=None):
    """
    Calls the Gemini API to review code, logs the request latency and status,
    and returns parsed results and scores.
    """
    start_time = time.time()
    
    # Check if API Key is configured
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE" or api_key.startswith("YOUR_"):
        latency = int((time.time() - start_time) * 1000)
        APILog.objects.create(
            user=user,
            language=language,
            latency_ms=latency,
            status='FAILED',
            error_message="Gemini API Key is not set or is still a placeholder in .env",
            prompt_length=len(code),
            response_length=0
        )
        return {
            'success': False,
            'error': "Gemini API Key is not configured. Please add your GEMINI_API_KEY to the .env file at the project root.",
            'text': "",
            'improved_code': "",
            'scores': {'security': 0, 'performance': 0, 'readability': 0, 'overall': 0}
        }
        
    try:
        # Configure SDK
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are an elite senior software architect, cybersecurity expert, and clean code reviewer.

Analyze the following {language} code deeply.

You must provide your review in beautiful markdown format. Your output MUST follow this exact structure:

# AI Code Review Report

## 1. Overall Code Summary
Explain what the code does.

## 2. Bugs and Logical Errors
Find syntax issues, logical problems, hidden bugs, and runtime risks.

## 3. Security Vulnerabilities
Check for:
- SQL Injection, XSS, CSRF
- Hardcoded Secrets
- Unsafe API usage
- Authentication & Authorization issues

## 4. Performance Optimization
Suggest:
- Better algorithms and loops
- Memory optimization
- Faster execution

## 5. Clean Code Suggestions
Check:
- Naming conventions
- Function structure, readability, and reusability
- SOLID principles

## 6. Best Practices
Provide industry-level best practices.

## 7. Improved Version
Generate an improved version of the code inside a Markdown code block with syntax highlighting.

## 8. Scores Summary
- **Security Score**: [SECURITY: X/10]
- **Performance Score**: [PERFORMANCE: X/10]
- **Readability Score**: [READABILITY: X/10]
- **Overall Score**: [OVERALL: X/10]

Where X is an integer score from 0 to 10. Make sure the labels `[SECURITY: X/10]`, `[PERFORMANCE: X/10]`, `[READABILITY: X/10]`, and `[OVERALL: X/10]` appear exactly as shown, replacing X with the numeric score.

Code:
```{language}
{code}
```
"""
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Parse scores using regex
        security_score = 0
        performance_score = 0
        readability_score = 0
        overall_score = 0
        
        sec_match = re.search(r'\[SECURITY:\s*(\d+)/10\]', response_text, re.IGNORECASE)
        perf_match = re.search(r'\[PERFORMANCE:\s*(\d+)/10\]', response_text, re.IGNORECASE)
        read_match = re.search(r'\[READABILITY:\s*(\d+)/10\]', response_text, re.IGNORECASE)
        overall_match = re.search(r'\[OVERALL:\s*(\d+)/10\]', response_text, re.IGNORECASE)
        
        if sec_match:
            security_score = min(max(int(sec_match.group(1)), 0), 10)
        if perf_match:
            performance_score = min(max(int(perf_match.group(1)), 0), 10)
        if read_match:
            readability_score = min(max(int(read_match.group(1)), 0), 10)
        if overall_match:
            overall_score = min(max(int(overall_match.group(1)), 0), 10)
            
        # Parse improved code block from section 7
        improved_code = ""
        section_7_match = re.search(r'## 7\.\s*Improved\s*Version([\s\S]*?)(?:## 8\.\s*Scores\s*Summary|\Z)', response_text, re.IGNORECASE)
        if section_7_match:
            section_7_text = section_7_match.group(1)
            code_block_match = re.search(r'```(?:[a-zA-Z0-9+#\-]+)?\n([\s\S]*?)\n```', section_7_text)
            if code_block_match:
                improved_code = code_block_match.group(1).strip()

        latency = int((time.time() - start_time) * 1000)
        
        # Save Success Log
        APILog.objects.create(
            user=user,
            language=language,
            latency_ms=latency,
            status='SUCCESS',
            prompt_length=len(prompt),
            response_length=len(response_text)
        )
        
        return {
            'success': True,
            'error': "",
            'text': response_text,
            'improved_code': improved_code,
            'scores': {
                'security': security_score,
                'performance': performance_score,
                'readability': readability_score,
                'overall': overall_score
            }
        }
        
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
        # Save Failed Log
        APILog.objects.create(
            user=user,
            language=language,
            latency_ms=latency,
            status='FAILED',
            error_message=error_msg,
            prompt_length=len(code),
            response_length=0
        )
        
        return {
            'success': False,
            'error': f"An error occurred while calling the Gemini API: {error_msg}",
            'text': "",
            'improved_code': "",
            'scores': {'security': 0, 'performance': 0, 'readability': 0, 'overall': 0}
        }


def chat_follow_up(review, message_history, user_message, user=None):
    """
    Submits follow-up conversation about a specific CodeReview to Gemini,
    persisting logs and returning the text response.
    """
    start_time = time.time()
    
    # Check if API Key is configured
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE" or api_key.startswith("YOUR_"):
        return {
            'success': False,
            'error': "Gemini API Key is not configured. Please add your GEMINI_API_KEY to the .env file."
        }
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Format the system instruction and original code review report as initial context
        system_context = f"""You are a helpful senior developer assistant answering follow-up questions about a code review you performed.

Here are the details of the original review:
- Language: {review.language}
- Submitted Code:
```
{review.code}
```

- Your initial review report was:
{review.ai_review}

If the user asks you to explain, correct, rewrite, or optimize code, you should answer clearly. Write clean markdown code blocks with correct syntax highlighting for any code you write."""

        # Construct Gemini API content structure (chat history)
        contents = [
            {"role": "user", "parts": [system_context]},
            {"role": "model", "parts": ["Understood. I have access to the original code and the review report, and will help the user with any follow-up questions they have. Please provide the user's first query."]}
        ]
        
        # Append existing chat history
        for msg in message_history:
            role = "user" if msg.role == 'user' else "model"
            contents.append({"role": role, "parts": [msg.content]})
            
        # Append the new user message
        contents.append({"role": "user", "parts": [user_message]})
        
        response = model.generate_content(contents)
        response_text = response.text
        
        latency = int((time.time() - start_time) * 1000)
        
        # Save Log
        APILog.objects.create(
            user=user,
            language=f"{review.language}-chat",
            latency_ms=latency,
            status='SUCCESS',
            prompt_length=sum(len(part) for content in contents for part in content["parts"]),
            response_length=len(response_text)
        )
        
        return {
            'success': True,
            'error': "",
            'text': response_text
        }
        
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        
        APILog.objects.create(
            user=user,
            language=f"{review.language}-chat",
            latency_ms=latency,
            status='FAILED',
            error_message=error_msg,
            prompt_length=len(user_message),
            response_length=0
        )
        
        return {
            'success': False,
            'error': f"An error occurred while communicating with Gemini API: {error_msg}"
        }
