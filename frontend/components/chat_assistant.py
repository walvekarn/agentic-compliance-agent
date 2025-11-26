"""
Chat Assistant Component
=========================
Reusable chat interface for asking questions about compliance decisions.
"""

import streamlit as st
from datetime import datetime
from .api_client import APIClient, display_api_error


def initialize_chat_state():
    """Initialize chat-related session state variables"""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_context" not in st.session_state:
        st.session_state.chat_context = {}
    if "chat_pending_question" not in st.session_state:
        st.session_state.chat_pending_question = ""


def process_chat_query(user_query: str, current_page: str, system_prompt: str):
    """
    Process a chat query and add response to chat messages.
    
    Args:
        user_query: The user's question
        current_page: Current page name
        system_prompt: System prompt for the page
    """
    # Prepare context-aware query with page-specific system prompt
    context = st.session_state.chat_context
    
    # Build context parts
    context_parts = [f"System: {system_prompt}"]
    
    # Add page/entity context if available
    if context:
        if context.get("page"):
            context_parts.append(f"Current Page: {context['page']}")
        if context.get("entity_name"):
            context_parts.append(f"Entity: {context['entity_name']}")
        if context.get("task_description"):
            context_parts.append(f"Task: {context['task_description'][:200]}")
        if context.get("decision"):
            context_parts.append(f"Decision: {context['decision']}")
        if context.get("risk_level"):
            context_parts.append(f"Risk: {context['risk_level']}")
    
    # Combine system prompt, context, and user query
    enhanced_query = (
        f"{chr(10).join(context_parts)}\n\n"
        f"User Question: {user_query}"
    )
    
    # Prepare chat history for API
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.chat_messages[:-1]  # Exclude the current message
    ]
    
    # Call API
    try:
        client = APIClient()
        response = client.post(
            "/api/v1/query",
            {
                "query": enhanced_query,
                "chat_history": chat_history if chat_history else None
            },
            timeout=30
        )
        
        if response.success:
            result = response.data or {}
            ai_response = result.get("response", "No response received")
            
            # Add AI response to chat with page tag
            timestamp = datetime.now().strftime("%I:%M %p")
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": timestamp,
                "page": current_page
            })
        else:
            error_msg = response.error or "❌ Error"
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "page": current_page
            })
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": error_msg,
            "timestamp": datetime.now().strftime("%I:%M %p"),
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
                "You are helping a user navigate the compliance dashboard. "
                "Provide guidance on which features to use, how the system works, "
                "and what each section does. Be welcoming and help them get started. "
                "Focus on navigation, overview, and general system capabilities."
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
                "You are helping a user fill out a compliance task analysis form. "
                "Guide them through the form fields, explain what information is needed, "
                "help clarify requirements, and answer questions about their specific situation. "
                "Focus on form completion, field requirements, and task-specific guidance. "
                "If they have context about their company or task, reference it in your answers."
            ),
            "suggestions": [
                "What information do I need to provide?",
                "How do I describe my task properly?",
                "What does 'Type of Organization' mean?",
                "Which industry should I select?",
                "What if my task involves multiple jurisdictions?",
                "How do I know if data is 'personal' or 'financial'?",
                "What impact level should I choose?",
                "Can you explain the form fields?"
            ]
        },
        "Audit Trail": {
            "system_prompt": (
                "You are helping a user understand past compliance decisions in the audit trail. "
                "Explain decision reasoning, risk factors, confidence scores, and historical patterns. "
                "Help them interpret audit records, understand why decisions were made, "
                "and identify trends. Focus on analysis, interpretation, and learning from history."
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
    Render the chat assistant panel
    
    Args:
        context_data: Optional dict with context about current page/decision
                     (e.g., page='Analyze Task', entity_name, task_description)
    """
    initialize_chat_state()
    
    # Update context if provided
    if context_data:
        st.session_state.chat_context.update(context_data)
    
    # Get page-specific context and suggestions
    system_prompt, suggested_questions = get_page_context(context_data)
    
    # Chat container with custom styling
    st.markdown("""
    <style>
        /* Chat panel styling */
        .chat-panel {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 15px;
            padding: 1rem;
            border: 2px solid #cbd5e1;
            max-height: 600px;
            overflow-y: auto;
        }
        
        /* Chat messages */
        .stChatMessage {
            margin-bottom: 0.75rem !important;
        }
        
        /* Input box */
        .stChatInputContainer {
            padding-top: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat header with enhanced visibility
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
        <h3 style='color: white; margin: 0; text-align: center;'>💬 AI Assistant</h3>
        <p style='color: white; margin: 0.5rem 0 0 0; text-align: center; font-size: 0.9rem;'>
            Ask questions about compliance, decisions, or how to use this tool
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Explicit messaging that chat is global
    st.info("💬 **Global Conversation** - Your chat history is saved across all pages", icon="ℹ️")
    st.caption("Ask questions about compliance decisions, clarifications, or summaries")
    
    # Current page indicator
    current_page = context_data.get("page", "Unknown") if context_data else "Unknown"
    st.markdown(f"**Current Page:** `{current_page}`")
    
    # Show context info if available
    if st.session_state.chat_context:
        with st.expander("📋 Current Page Context", expanded=False):
            context = st.session_state.chat_context
            if context.get("page"):
                st.caption(f"**Page:** {context['page']}")
            if context.get("entity_name"):
                st.caption(f"**Entity:** {context['entity_name']}")
            if context.get("task_description"):
                st.caption(f"**Task:** {context['task_description'][:100]}...")
            if context.get("decision"):
                st.caption(f"**Decision:** {context['decision']}")
    
    # Message count indicator
    if st.session_state.chat_messages:
        total_messages = len(st.session_state.chat_messages)
        user_messages = len([m for m in st.session_state.chat_messages if m.get("role") == "user"])
        st.caption(f"📊 {total_messages} messages ({user_messages} from you)")
    
    # Display chat history with page tags
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show page context for message
            metadata_parts = []
            if message.get("timestamp"):
                metadata_parts.append(message['timestamp'])
            if message.get("page"):
                metadata_parts.append(f"📍 {message['page']}")
            
            if metadata_parts:
                st.caption(f"_{' • '.join(metadata_parts)}_")
    
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
        
        # Add user message to chat with page tag
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_query,
            "timestamp": timestamp,
            "page": current_page  # Tag message with current page
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
            st.caption(f"_{timestamp} • 📍 {current_page}_")
        
        # Process the query using helper function
        with st.spinner("🤔 AI is thinking..."):
            process_chat_query(user_query, current_page, system_prompt)
        
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
            if st.button(suggestion, key=f"suggest_btn_{idx}", width="stretch"):
                # Set pending question and trigger chat submission
                st.session_state.chat_pending_question = suggestion
                # Add user message immediately
                timestamp = datetime.now().strftime("%I:%M %p")
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": suggestion,
                    "timestamp": timestamp,
                    "page": current_page
                })
                # Process the query
                process_chat_query(suggestion, current_page, system_prompt)
                st.rerun()
    
    # Chat controls
    st.markdown("---")
    
    # Clear chat button with explicit warning
    if st.session_state.chat_messages:
        with st.expander("⚙️ Chat Management", expanded=False):
            st.warning("⚠️ **Warning**: Clearing chat will delete ALL conversation history across ALL pages")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("🗑️ Clear All History", width="stretch", help="Delete all chat messages from all pages", type="secondary"):
                    st.session_state.chat_messages = []
                    st.session_state.chat_context = {}
                    st.success("✅ Chat history cleared!")
                    st.rerun()
            
            with col2:
                # Filter to current page only
                messages_on_page = len([m for m in st.session_state.chat_messages if m.get("page") == current_page])
                if st.button(f"🗑️ Clear {current_page} Only", width="stretch", help=f"Delete only messages from {current_page}", type="secondary"):
                    st.session_state.chat_messages = [
                        m for m in st.session_state.chat_messages 
                        if m.get("page") != current_page
                    ]
                    st.success(f"✅ Cleared {messages_on_page} messages from {current_page}!")
                    st.rerun()
    
    # Export button
    st.markdown("---")
    
    if st.session_state.chat_messages:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show statistics
            pages_used = set([m.get("page", "Unknown") for m in st.session_state.chat_messages])
            st.caption(f"💬 Messages across {len(pages_used)} page(s): {', '.join(sorted(pages_used))}")
        
        with col2:
            # Export chat history with page tags
            chat_export = "\n\n".join([
                f"{msg['role'].upper()} ({msg.get('timestamp', 'N/A')}) [Page: {msg.get('page', 'Unknown')}]:\n{msg['content']}"
                for msg in st.session_state.chat_messages
            ])
            
            st.download_button(
                label="💾 Export",
                data=chat_export,
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                width="stretch",
                help="Download chat history as text file"
            )


def render_chat_sidebar():
    """
    Render chat in sidebar (alternative layout)
    """
    with st.sidebar:
        st.markdown("---")
        render_chat_panel()
