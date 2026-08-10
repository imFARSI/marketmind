# AI Companion Chat (Role Restricted to Business Owner / Business User)

import os
import requests
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, CompanionMessage, Business

ai_chat_bp = Blueprint('salman_ai_chat', __name__, url_prefix='/salman/ai-companion')

DEFAULT_NVIDIA_KEY = "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"
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', DEFAULT_NVIDIA_KEY)
NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def get_user_business():
    if current_user.role == 'Field Agent' and current_user.business_id:
        return Business.query.get(current_user.business_id)
    business = Business.query.filter_by(owner_id=current_user.id).first()
    if not business:
        import secrets
        code = f"BIZ{secrets.randbelow(8999) + 1000}"
        business = Business(name=f"{current_user.username}'s Business", industry="General", join_code=code, owner_id=current_user.id)
        db.session.add(business)
        db.session.commit()
    return business

def perform_web_search(query):
    """Simple web search tool using DuckDuckGo HTML API for 2026 real-time web facts."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}", headers=headers, timeout=3)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            for a in soup.find_all('a', class_='result__snippet', limit=3):
                results.append(a.get_text())
            if results:
                return "\n".join(results)
    except Exception:
        pass
    return ""

def query_nvidia_llama(prompt, conversation_history=None):
    """Queries NVIDIA NIM API hosting Meta Llama 3.1 8B Instruct model for ultra-fast response times."""
    api_key = os.getenv('NVIDIA_API_KEY') or DEFAULT_NVIDIA_KEY
    if not api_key:
        return "NVIDIA API key not configured in .env file."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Check if prompt requires live web search
    search_keywords = ['latest', 'news', 'today', '2026', 'current', 'stock', 'who is', 'trend']
    web_context = ""
    if any(kw in prompt.lower() for kw in search_keywords):
        search_snippet = perform_web_search(prompt)
        if search_snippet:
            web_context = f"\n[Live Web Search Context (2026)]:\n{search_snippet}\n"

    system_message = {
        "role": "system",
        "content": "You are MarketMind AI, a helpful, intelligent, general Ask-Anything AI assistant powered by Meta Llama 3.1 8B on NVIDIA NIM infrastructure. Answer questions clearly, accurately, and concisely."
    }

    messages = [system_message]

    if conversation_history:
        for msg in conversation_history[-4:]:
            role = "assistant" if msg.sender.lower() == 'ai' else "user"
            messages.append({"role": role, "content": msg.message})

    final_user_content = f"{web_context}{prompt}" if web_context else prompt
    messages.append({"role": "user", "content": final_user_content})

    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": messages,
        "temperature": 0.6,
        "top_p": 0.9,
        "max_tokens": 512
    }

    try:
        response = requests.post(NVIDIA_NIM_URL, headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        else:
            return "Ask me again, I'm having a network issue."
    except Exception:
        return "Ask me again, I'm having a network issue."

@ai_chat_bp.route('/')
@login_required
def index():
    if current_user.role == 'Field Agent':
        flash('Access denied. Field agents do not have access to AI Companion.', 'danger')
        return redirect(url_for('salman_field_tasks.my_tasks'))

    business = get_user_business()
    messages = CompanionMessage.query.filter_by(business_id=business.id).order_by(CompanionMessage.created_at.asc()).all()
    return render_template('salman/ai_chat.html', messages=messages)

@ai_chat_bp.route('/history')
@login_required
def get_history():
    if current_user.role == 'Field Agent':
        return jsonify({'error': 'Access denied. Field Agents cannot access AI Companion.'}), 403

    business = get_user_business()
    messages = CompanionMessage.query.filter_by(business_id=business.id).order_by(CompanionMessage.created_at.asc()).all()
    data = []
    for msg in messages:
        data.append({
            'sender': msg.sender,
            'message': msg.message,
            'timestamp': msg.created_at.strftime('%H:%M')
        })
    return jsonify({'messages': data})

@ai_chat_bp.route('/send', methods=['POST'])
@ai_chat_bp.route('/message', methods=['POST'])
@login_required
def send_message():
    if current_user.role == 'Field Agent':
        return jsonify({'error': 'Access denied. Field Agents cannot access AI Companion.'}), 403

    business = get_user_business()
    payload = request.get_json(silent=True) or request.form
    user_prompt = payload.get('prompt', '').strip()

    if not user_prompt:
        return jsonify({'error': 'Empty prompt'}), 400

    user_msg = CompanionMessage(
        sender=current_user.username,
        message=user_prompt,
        business_id=business.id
    )
    db.session.add(user_msg)
    db.session.commit()

    history = CompanionMessage.query.filter_by(business_id=business.id).order_by(CompanionMessage.created_at.asc()).all()

    ai_response_text = query_nvidia_llama(user_prompt, conversation_history=history)

    ai_msg = CompanionMessage(
        sender='AI',
        message=ai_response_text,
        business_id=business.id
    )
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'user_prompt': user_prompt,
        'ai_response': ai_response_text,
        'timestamp': ai_msg.created_at.strftime('%H:%M')
    })

@ai_chat_bp.route('/clear', methods=['POST'])
@login_required
def clear_history():
    if current_user.role == 'Field Agent':
        flash('Access denied.', 'danger')
        return redirect(url_for('salman_field_tasks.my_tasks'))

    business = get_user_business()
    CompanionMessage.query.filter_by(business_id=business.id).delete()
    db.session.commit()
    flash('AI Companion chat history cleared.', 'info')
    return redirect(url_for('salman_ai_chat.index'))
