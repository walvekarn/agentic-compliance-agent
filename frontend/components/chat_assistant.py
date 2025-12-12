"""
Chat Assistant Component
=========================
Reusable chat interface for asking questions about compliance decisions.
"""

import streamlit as st
from datetime import datetime
from .api_client import APIClient, display_api_error


def initialize_chat_state(page_name: str):
    """
    Initialize chat-related session state variables with page-specific isolation.
    
    Args:
        page_name: Current page name for isolating chat history
    """
    # Use page-specific keys for chat messages
    chat_key = f"chat_messages_{page_name}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    # Use page-specific context
    context_key = f"chat_context_{page_name}"
    if context_key not in st.session_state:
        st.session_state[context_key] = {}
    
    if "chat_pending_question" not in st.session_state:
        st.session_state.chat_pending_question = ""


def process_chat_query(user_query: str, current_page: str, system_prompt: str, context_data: dict = None):
    """
    Process a chat query and add response to chat messages with page-specific isolation.
    
    Args:
        user_query: The user's question
        current_page: Current page name
        system_prompt: System prompt for the page
        context_data: Additional context data from the current page
    """
    # Get page-specific context
    context_key = f"chat_context_{current_page}"
    context = st.session_state.get(context_key, {})
    
    # Update context with provided data
    if context_data:
        context.update(context_data)
        st.session_state[context_key] = context
    
    # Build comprehensive context parts for better relevance
    context_parts = [f"System: {system_prompt}"]
    
    # Add page/entity context if available
    if context:
        if context.get("page"):
            context_parts.append(f"Current Page: {context['page']}")
        if context.get("entity_name"):
            context_parts.append(f"Entity: {context['entity_name']}")
        if context.get("task_description"):
            # Include more of the task description for better context
            task_desc = context['task_description']
            if len(task_desc) > 300:
                task_desc = task_desc[:300] + "..."
            context_parts.append(f"Task: {task_desc}")
        if context.get("decision"):
            context_parts.append(f"Recent Decision: {context['decision']}")
        if context.get("risk_level"):
            context_parts.append(f"Risk Level: {context['risk_level']}")
        if context.get("form_data"):
            # Include relevant form data if available
            form_data = context['form_data']
            if isinstance(form_data, dict):
                relevant_fields = []
                for key in ['industry', 'company_type', 'locations', 'task_type']:
                    if key in form_data and form_data[key]:
                        relevant_fields.append(f"{key}: {form_data[key]}")
                if relevant_fields:
                    context_parts.append(f"Form Context: {', '.join(relevant_fields)}")
    
    # Combine system prompt, context, and user query with clear structure
    enhanced_query = (
        f"{chr(10).join(context_parts)}\n\n"
        f"User Question: {user_query}\n\n"
        f"Please provide a clear, relevant answer based on the context above."
    )
    
    # Get page-specific chat history
    chat_key = f"chat_messages_{current_page}"
    page_chat_messages = st.session_state.get(chat_key, [])
    
    # Prepare chat history for API (exclude the current message if it was already added)
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in page_chat_messages[:-1]  # Exclude the current message
    ]
    
    # Call API
    # Pass original user query separately for audit logging (without system prompts)
    try:
        client = APIClient()
        response = client.post(
            "/api/v1/query",
            {
                "query": enhanced_query,  # Enhanced query with system prompts for LLM processing
                "chat_history": chat_history if chat_history else None,
                "original_user_query": user_query  # Original user query for audit logging
            },
            timeout=30
        )
        
        if response.success:
            result = response.data or {}
            ai_response = result.get("response", "No response received")
            
            # Add AI response to page-specific chat
            chat_key = f"chat_messages_{current_page}"
            timestamp = datetime.now().strftime("%I:%M %p")
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []
            st.session_state[chat_key].append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": timestamp,
                "page": current_page
            })
        else:
            error_msg = response.error or "❌ Error"
            chat_key = f"chat_messages_{current_page}"
            timestamp = datetime.now().strftime("%I:%M %p")
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []
            st.session_state[chat_key].append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": timestamp,
                "page": current_page
            })
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        chat_key = f"chat_messages_{current_page}"
        timestamp = datetime.now().strftime("%I:%M %p")
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": error_msg,
            "timestamp": timestamp,
            "page": current_page
        })


def get_page_context(context_data):
    """
    Get page-specific context and system prompt based on current page
    
    Args:
        context_data: Dict with 'page' key indicating current page
        
    Returns:
        Tuple of (system_prompt, suggested_questions)
    """
    page = context_data.get("page", "Home") if context_data else "Home"
    
    page_contexts = {
        "Home": {
            "system_prompt": (
                "You are a helpful AI assistant for a compliance dashboard. "
                "Your role is to guide users through the system, explain features, and help them get started. "
                "\n\n"
                "When answering questions:\n"
                "- Explain how to navigate between different pages and features\n"
                "- Describe what each section of the dashboard does\n"
                "- Guide users on which tools to use for their specific compliance needs\n"
                "- Provide clear, step-by-step instructions when needed\n"
                "- Be welcoming and encouraging, especially for new users\n"
                "\n"
                "Focus on navigation, overview, and helping users understand the system's capabilities."
            ),
            "suggestions": [
                "How do I get started with this dashboard?",
                "What can this compliance assistant help me with?",
                "How do I check if I can do a task myself?",
                "Where can I see past compliance decisions?",
                "How does the AI agent make decisions?",
                "What's the difference between the pages?",
                "Can I see examples of how this works?",
                "Who should use this dashboard?"
            ]
        },
        "Analyze Task": {
            "system_prompt": (
                "You are an expert compliance assistant helping users analyze compliance tasks. "
                "You help users fill out the task analysis form by explaining what information is needed, "
                "clarifying requirements, and providing guidance based on their specific situation. "
                "\n\n"
                "When answering questions:\n"
                "- Reference specific form fields and their purposes\n"
                "- Provide examples relevant to the user's industry or task type\n"
                "- Explain how different choices affect the compliance analysis\n"
                "- Help users understand jurisdiction requirements and their implications\n"
                "- Guide users on how to describe their task clearly and completely\n"
                "- If context about the user's company, industry, or task is provided, use it to give personalized guidance\n"
                "\n"
                "Focus on practical, actionable advice that helps users complete the form accurately."
            ),
            "suggestions": [
                "What information do I need to provide in this form?",
                "How should I describe my compliance task?",
                "What does 'Type of Organization' mean and which should I choose?",
                "How do I select the right industry for my company?",
                "What if my task involves multiple jurisdictions?",
                "How do I determine if data is 'personal' or 'financial'?",
                "What impact level should I choose and why?",
                "Can you explain what each form field means?"
            ]
        },
        "Audit Trail": {
            "system_prompt": (
                "You are an expert compliance analyst helping users understand past compliance decisions in the audit trail. "
                "Your role is to explain decision reasoning, risk factors, confidence scores, and historical patterns. "
                "\n\n"
                "When answering questions:\n"
                "- Explain why specific decisions were made based on the reasoning chain\n"
                "- Interpret risk factors and their implications\n"
                "- Clarify confidence scores and what they mean\n"
                "- Identify patterns and trends across multiple audit entries\n"
                "- Help users understand how past decisions relate to current situations\n"
                "- If context about specific audit entries is provided, reference it directly\n"
                "\n"
                "Focus on analysis, interpretation, and helping users learn from historical compliance decisions."
            ),
            "suggestions": [
                "Why was this decision made?",
                "What do the risk factors mean?",
                "How confident was the AI in this decision?",
                "What patterns can I see in past decisions?",
                "Why are some tasks escalated and others not?",
                "What should I look for in the audit trail?",
                "How can I filter for specific types of decisions?",
                "What does the reasoning chain tell me?"
            ]
        },
        "Compliance Calendar": {
            "system_prompt": (
                "You are helping a user understand their compliance schedule and upcoming tasks. "
                "Explain deadlines, task priorities, frequency requirements, and calendar management. "
                "Help them plan their compliance activities and understand what needs to be done when. "
                "Focus on scheduling, deadlines, priorities, and task planning."
            ),
            "suggestions": [
                "What tasks are coming up soon?",
                "How often do I need to do this task?",
                "What happens if I miss a deadline?",
                "Which tasks are most urgent?",
                "How do I plan my compliance work?",
                "What are the different task frequencies?",
                "Can you explain the task priorities?",
                "How far ahead should I plan?"
            ]
        },
        "Agent Insights": {
            "system_prompt": (
                "You are helping a user understand AI agent performance metrics and analytics. "
                "Explain confidence trends, escalation patterns, accuracy metrics, and learning progress. "
                "Help them interpret charts, understand agent behavior, and assess system performance. "
                "Focus on metrics, trends, patterns, and performance analysis."
            ),
            "suggestions": [
                "How is the AI agent performing?",
                "What do the confidence scores mean?",
                "Why are decisions being escalated?",
                "How accurate is the AI agent?",
                "What patterns can I see in the data?",
                "How is the agent learning over time?",
                "What do the risk factor charts show?",
                "How can I improve AI accuracy?"
            ]
        }
    }
    
    # Default to generic context if page not found
    default_context = {
        "system_prompt": (
            "You are a helpful AI assistant for a compliance dashboard. "
            "Answer questions about compliance decisions, processes, and requirements. "
            "Provide clear, practical guidance."
        ),
        "suggestions": [
            "Explain this in simple terms",
            "What should I do next?",
            "Why is this important?",
            "How does this work?",
            "What are the main points?",
            "Can you give me an example?",
            "What happens if I disagree?",
            "Where can I learn more?"
        ]
    }
    
    page_info = page_contexts.get(page, default_context)
    return page_info["system_prompt"], page_info["suggestions"]


def render_chat_panel(context_data=None):
    """
    Render the chat assistant panel with page-specific isolation
    
    Args:
        context_data: Optional dict with context about current page/decision
                     (e.g., page='Analyze Task', entity_name, task_description, form_data)
    """
    # Get current page name
    current_page = context_data.get("page", "Home") if context_data else "Home"
    
    # Initialize page-specific chat state
    initialize_chat_state(current_page)
    
    # Update page-specific context if provided
    if context_data:
        context_key = f"chat_context_{current_page}"
        if context_key not in st.session_state:
            st.session_state[context_key] = {}
        st.session_state[context_key].update(context_data)
    
    # Get page-specific context and suggestions
    system_prompt, suggested_questions = get_page_context(context_data)
    
    # Chat container with light theme styling
    st.markdown("""
    <style>
        /* Chat panel styling - Light Theme */
        .chat-panel {
            background: #ffffff !important;
            border-radius: 15px;
            padding: 1rem;
            border: 2px solid #e2e8f0 !important;
            max-height: 600px;
            overflow-y: auto;
        }
        
        /* Chat messages - Light Theme */
        .stChatMessage {
            margin-bottom: 0.75rem !important;
            background-color: #ffffff !important;
        }
        
        /* Input box */
        .stChatInputContainer {
            padding-top: 0.5rem;
            background-color: #ffffff !important;
        }
        
        /* Current Page Indicator - Light Theme */
        .chat-page-indicator {
            background: #f1f5f9 !important;
            color: #1e293b !important;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: 1px solid #cbd5e1 !important;
            margin: 0.5rem 0;
        }
        
        /* Chat header - Light Theme */
        .chat-header {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
            color: #0f172a !important;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border: 1px solid #cbd5e1 !important;
        }
        
        .chat-header h3 {
            color: #0f172a !important;
        }
        
        .chat-header p {
            color: #0f172a !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat header with light theme styling
    st.markdown(f"""
    <div class='chat-header'>
        <h3 style='color: #0f172a !important; margin: 0; text-align: center;'>💬 AI Assistant</h3>
        <p style='color: #0f172a !important; margin: 0.5rem 0 0 0; text-align: center; font-size: 0.9rem;'>
            Ask questions about compliance, decisions, or how to use this tool
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Page-specific messaging
    st.info(f"💬 **Page-Specific Chat** - Your conversation on '{current_page}' is isolated from other pages", icon="ℹ️")
    st.caption("Ask questions about compliance decisions, clarifications, or summaries specific to this page")
    
    # Current page indicator with light theme
    st.markdown(f"""
    <div class='chat-page-indicator'>
        <strong>Current Page:</strong> <code style='background: #e2e8f0; color: #0f172a; padding: 0.2rem 0.4rem; border-radius: 4px;'>{current_page}</code>
    </div>
    """, unsafe_allow_html=True)
    
    # Show context info if available
    context_key = f"chat_context_{current_page}"
    context = st.session_state.get(context_key, {})
    if context:
        with st.expander("📋 Current Page Context", expanded=False):
            if context.get("page"):
                st.caption(f"**Page:** {context['page']}")
            if context.get("entity_name"):
                st.caption(f"**Entity:** {context['entity_name']}")
            if context.get("task_description"):
                st.caption(f"**Task:** {context['task_description'][:100]}...")
            if context.get("decision"):
                st.caption(f"**Decision:** {context['decision']}")
            if context.get("form_data"):
                st.caption("**Form Data:** Available")
    
    # Get page-specific chat messages
    chat_key = f"chat_messages_{current_page}"
    page_chat_messages = st.session_state.get(chat_key, [])
    
    # Message count indicator
    if page_chat_messages:
        total_messages = len(page_chat_messages)
        user_messages = len([m for m in page_chat_messages if m.get("role") == "user"])
        st.caption(f"📊 {total_messages} messages on this page ({user_messages} from you)")
    
    # Display page-specific chat history
    for message in page_chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(f"""
            <div style="background-color: #2d2d3d; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #404050;">
                <p style="color: #e0e0e0; margin: 0;">{message["content"]}</p>
            </div>
            """, unsafe_allow_html=True)
            if message.get("timestamp"):
                st.caption(f"_{message['timestamp']}_")
    
    # Chat input - simple text input with pending question from suggestions
    user_query = st.text_input(
        "Ask a question about compliance...", 
        key="chat_input_sidebar",
        value=st.session_state.chat_pending_question
    )
    
    # Button to submit
    submit_chat = st.button("Send", key="send_chat_btn", width="stretch")
    
    # Process on button click - check if there's a query in the text input
    if submit_chat and user_query and user_query.strip():
        # Clear pending question after use
        st.session_state.chat_pending_question = ""
        
        # Add user message to page-specific chat
        chat_key = f"chat_messages_{current_page}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state[chat_key].append({
            "role": "user",
            "content": user_query,
            "timestamp": timestamp,
            "page": current_page
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(f"""
            <div style="background-color: #2d2d3d; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #404050;">
                <p style="color: #e0e0e0; margin: 0;">{user_query}</p>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"_{timestamp}_")
        
        # Process the query using helper function with context data
        with st.spinner("🤔 AI is thinking..."):
            process_chat_query(user_query, current_page, system_prompt, context_data)
        
        # Rerun to display the new messages
        st.rerun()
    
    # Suggested questions section (page-specific)
    st.markdown("---")
    with st.expander("💡 Suggested Questions", expanded=False):
        current_page = context_data.get("page", "Home") if context_data else "Home"
        st.caption(f"Click any question to ask the AI (tailored for {current_page}):")
        
        # Use page-specific suggestions
        suggestions = suggested_questions
        
        for idx, suggestion in enumerate(suggestions):
            if st.button(suggestion, key=f"suggest_btn_{idx}_{current_page}", width="stretch"):
                # Add user message to page-specific chat
                chat_key = f"chat_messages_{current_page}"
                if chat_key not in st.session_state:
                    st.session_state[chat_key] = []
                
                timestamp = datetime.now().strftime("%I:%M %p")
                st.session_state[chat_key].append({
                    "role": "user",
                    "content": suggestion,
                    "timestamp": timestamp,
                    "page": current_page
                })
                # Process the query with context data
                process_chat_query(suggestion, current_page, system_prompt, context_data)
                st.rerun()
    
    # Chat controls
    st.markdown("---")
    
    # Get page-specific chat messages for management
    chat_key = f"chat_messages_{current_page}"
    page_chat_messages = st.session_state.get(chat_key, [])
    
    # Clear chat button - page-specific
    if page_chat_messages:
        with st.expander("⚙️ Chat Management", expanded=False):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button(f"🗑️ Clear {current_page} Chat", width="stretch", help=f"Delete all chat messages from {current_page}", type="secondary"):
                    st.session_state[chat_key] = []
                    context_key = f"chat_context_{current_page}"
                    if context_key in st.session_state:
                        st.session_state[context_key] = {}
                    st.success(f"✅ Chat history cleared for {current_page}!")
                    st.rerun()
            
            with col2:
                # Get all pages with chat history
                all_chat_keys = [k for k in st.session_state.keys() if k.startswith("chat_messages_")]
                total_pages_with_chat = len(all_chat_keys)
                
                if total_pages_with_chat > 1 and st.button("🗑️ Clear All Pages", width="stretch", help="Delete chat history from all pages", type="secondary"):
                    st.warning("⚠️ This will clear chat history from ALL pages!")
                    for key in all_chat_keys:
                        del st.session_state[key]
                    # Also clear context keys
                    context_keys = [k for k in st.session_state.keys() if k.startswith("chat_context_")]
                    for key in context_keys:
                        del st.session_state[key]
                    st.success("✅ All chat history cleared!")
                    st.rerun()
    
    # Export button
    st.markdown("---")
    
    if page_chat_messages:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show statistics for this page
            user_messages = len([m for m in page_chat_messages if m.get("role") == "user"])
            st.caption(f"💬 {len(page_chat_messages)} messages on this page ({user_messages} from you)")
        
        with col2:
            # Export page-specific chat history
            chat_export = f"Chat Export - {current_page}\n"
            chat_export += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            chat_export += "=" * 50 + "\n\n"
            chat_export += "\n\n".join([
                f"{msg['role'].upper()} ({msg.get('timestamp', 'N/A')}):\n{msg['content']}"
                for msg in page_chat_messages
            ])
            
            st.download_button(
                label="💾 Export This Page",
                data=chat_export,
                file_name=f"chat_export_{current_page.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                width="stretch",
                help=f"Download chat history from {current_page}"
            )


def render_chat_sidebar():
    """
    Render chat in sidebar (alternative layout)
    """
    with st.sidebar:
        st.markdown("---")
        render_chat_panel()
