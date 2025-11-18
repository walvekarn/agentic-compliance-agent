"""
Export Utilities
=================
Comprehensive export functionality for dashboard data.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from io import BytesIO
from .api_client import APIClient, display_api_error

# Initialize session state for export history
def initialize_export_history():
    """Initialize export history in session state"""
    if "export_history" not in st.session_state:
        st.session_state.export_history = []


def add_to_export_history(filename: str, format: str, size_kb: float):
    """Add export to history"""
    initialize_export_history()
    
    export_record = {
        "filename": filename,
        "format": format,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size_kb": size_kb
    }
    
    # Add to beginning of list
    st.session_state.export_history.insert(0, export_record)
    
    # Keep only last 10 exports
    st.session_state.export_history = st.session_state.export_history[:10]


def generate_filename(
    prefix: str,
    entity_name: Optional[str] = None,
    task_category: Optional[str] = None,
    risk_level: Optional[str] = None,
    extension: str = "txt"
) -> str:
    """
    Generate smart filename with context
    
    Args:
        prefix: File prefix (e.g., "guidance", "calendar", "audit")
        entity_name: Optional entity name
        task_category: Optional task category
        risk_level: Optional risk level
        extension: File extension without dot
    
    Returns:
        Formatted filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    parts = [prefix]
    
    # Add context parts if provided
    if entity_name:
        # Clean entity name (remove spaces, special chars)
        clean_name = entity_name.replace(" ", "_").replace("/", "_")[:30]
        parts.append(clean_name)
    
    if task_category:
        clean_category = task_category.replace(" ", "_").replace("/", "_")[:20]
        parts.append(clean_category)
    
    if risk_level:
        parts.append(risk_level.upper())
    
    parts.append(timestamp)
    
    return f"{'_'.join(parts)}.{extension}"


def create_pdf_from_text(text_content: str, title: str) -> bytes:
    """
    Create a simple PDF from text content
    Note: This is a placeholder - real PDF generation would use reportlab or similar
    
    For now, returns formatted text that can be saved as PDF
    """
    # Simple PDF-like formatting (would use reportlab in production)
    pdf_content = f"""
================================================================================
{title}
================================================================================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================================

{text_content}

================================================================================
End of Report
================================================================================
"""
    return pdf_content.encode('utf-8')


def create_excel_from_dataframe(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    """
    Create Excel file with formatting from DataFrame
    
    Args:
        df: Pandas DataFrame
        sheet_name: Name for Excel sheet
    
    Returns:
        Excel file as bytes
    """
    output = BytesIO()
    
    # Create Excel writer with xlsxwriter engine for formatting
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B5563',
            'font_color': '#FFFFFF',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Auto-adjust column width
            column_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, min(column_len, 50))
    
    output.seek(0)
    return output.getvalue()


def render_export_section(
    data: Any,
    dataframe: Optional[pd.DataFrame] = None,
    text_report: Optional[str] = None,
    json_data: Optional[Dict] = None,
    prefix: str = "export",
    entity_name: Optional[str] = None,
    task_category: Optional[str] = None,
    risk_level: Optional[str] = None,
    show_email: bool = True,
    email_api_endpoint: Optional[str] = None
):
    """
    Render comprehensive export section with multiple format options
    
    Args:
        data: Primary data to export
        dataframe: Optional DataFrame for Excel export
        text_report: Optional text report
        json_data: Optional JSON data
        prefix: Filename prefix
        entity_name: Entity name for filename
        task_category: Task category for filename
        risk_level: Risk level for filename
        show_email: Whether to show email option
        email_api_endpoint: API endpoint for email functionality
    """
    initialize_export_history()
    
    st.markdown("### 💾 Export Options")
    st.caption("Download your data in multiple formats for easy sharing and integration")
    
    # Export format buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # TXT Export
        if text_report:
            filename_txt = generate_filename(prefix, entity_name, task_category, risk_level, "txt")
            
            if st.button("📄 Download TXT", use_container_width=True, help="Plain text report"):
                # This will trigger on next interaction
                st.session_state.pending_export = {
                    "type": "txt",
                    "data": text_report,
                    "filename": filename_txt
                }
    
    with col2:
        # Excel Export
        if dataframe is not None and not dataframe.empty:
            filename_excel = generate_filename(prefix, entity_name, task_category, risk_level, "xlsx")
            
            if st.button("📊 Download Excel", use_container_width=True, help="Excel with formatting"):
                st.session_state.pending_export = {
                    "type": "excel",
                    "data": dataframe,
                    "filename": filename_excel
                }
    
    with col3:
        # JSON Export
        if json_data:
            filename_json = generate_filename(prefix, entity_name, task_category, risk_level, "json")
            
            if st.button("📋 Download JSON", use_container_width=True, help="Raw JSON data"):
                st.session_state.pending_export = {
                    "type": "json",
                    "data": json_data,
                    "filename": filename_json
                }
    
    with col4:
        # PDF Export (placeholder)
        if text_report:
            filename_pdf = generate_filename(prefix, entity_name, task_category, risk_level, "pdf")
            
            if st.button("📕 Download PDF", use_container_width=True, help="PDF report"):
                st.session_state.pending_export = {
                    "type": "pdf",
                    "data": text_report,
                    "filename": filename_pdf
                }
    
    # Process pending export
    if hasattr(st.session_state, 'pending_export') and st.session_state.pending_export:
        export_info = st.session_state.pending_export
        export_type = export_info["type"]
        export_data = export_info["data"]
        export_filename = export_info["filename"]
        
        # Prepare data based on type
        if export_type == "txt":
            file_data = export_data.encode('utf-8')
            mime_type = "text/plain"
        elif export_type == "excel":
            file_data = create_excel_from_dataframe(export_data)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif export_type == "json":
            file_data = json.dumps(export_data, indent=2, default=str).encode('utf-8')
            mime_type = "application/json"
        elif export_type == "pdf":
            file_data = create_pdf_from_text(export_data, prefix.title())
            mime_type = "application/pdf"
        else:
            file_data = str(export_data).encode('utf-8')
            mime_type = "text/plain"
        
        # Calculate size
        size_kb = len(file_data) / 1024
        
        # Show download button
        st.download_button(
            label=f"💾 Click to Save {export_filename}",
            data=file_data,
            file_name=export_filename,
            mime=mime_type,
            use_container_width=True,
            type="primary"
        )
        
        # Success message
        st.success(f"✅ Export ready! **{export_filename}** ({size_kb:.1f} KB)")
        
        # Add to history
        add_to_export_history(export_filename, export_type.upper(), size_kb)
        
        # Clear pending export after displaying
        del st.session_state.pending_export
    
    # Email option
    if show_email and email_api_endpoint:
        st.markdown("---")
        st.markdown("#### 📧 Email This Report")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            recipient_email = st.text_input(
                "Recipient email address",
                placeholder="colleague@company.com",
                help="Send this report directly to an email address"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.button("📧 Send Email", use_container_width=True, disabled=not recipient_email):
                with st.spinner("Sending email..."):
                    try:
                        # Prepare email data
                        email_payload = {
                            "recipient": recipient_email,
                            "subject": f"Compliance Report: {prefix.title()}",
                            "body": text_report if text_report else "Please see attached compliance report.",
                            "attachment_data": json_data if json_data else {}
                        }
                        
                        # Send via API
                        api = APIClient()
                        response = api.post(email_api_endpoint.replace(APIClient().base_url, "") if email_api_endpoint.startswith(APIClient().base_url) else email_api_endpoint, email_payload, timeout=10)
                        
                        if response.success:
                            st.success(f"✅ Report sent to {recipient_email}!")
                        else:
                            display_api_error(response)
                    except Exception as e:
                        st.error(f"❌ Error sending email: {str(e)}")


def render_export_history():
    """Render export history in sidebar or expander"""
    initialize_export_history()
    
    if st.session_state.export_history:
        with st.expander(f"📦 Recent Exports ({len(st.session_state.export_history)})", expanded=False):
            st.caption("Your recent downloads")
            
            for export in st.session_state.export_history[:5]:  # Show last 5
                st.markdown(
                    f"**{export['format']}** • `{export['filename']}`  \n"
                    f"_{export['timestamp']} • {export['size_kb']:.1f} KB_"
                )
                st.markdown("---")
            
            if len(st.session_state.export_history) > 5:
                st.caption(f"+ {len(st.session_state.export_history) - 5} more exports")
            
            # Clear history button
            if st.button("🗑️ Clear Export History", use_container_width=True):
                st.session_state.export_history = []
                st.rerun()
    else:
        with st.expander("📦 Recent Exports (0)", expanded=False):
            st.info("No exports yet. Download a report to see it here!")

