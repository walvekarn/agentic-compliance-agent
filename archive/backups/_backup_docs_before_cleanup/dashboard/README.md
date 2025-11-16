# 🎨 Business Dashboard for AI Compliance Agent

**A user-friendly web interface for non-technical users**

---

## 🎯 Purpose

This dashboard provides a **point-and-click interface** for compliance analysts, managers, and business users who need to:
- Analyze compliance tasks without writing code
- Generate compliance calendars for organizations
- View and export audit trails
- Get instant risk assessments and recommendations

**No JSON, APIs, or technical knowledge required!**

---

## ✨ Features

### 1. **Home Page** 🏠
- Quick access to all features
- Real-time API status
- Live statistics dashboard

### 2. **Analyze Task** 🎯
- Simple form with dropdowns and checkboxes
- Instant AI risk assessment
- Clear decision: Autonomous, Review, or Escalate
- Complete reasoning chain
- Export results as JSON or TXT

### 3. **Compliance Calendar** 📋
- Generate full compliance calendar for any organization
- Automatic task generation based on industry and jurisdiction
- Risk levels and autonomy decisions for each task
- Filter and sort tasks
- Export to Excel, JSON, or TXT

### 4. **Audit Trail** 📊
- View all past decisions
- Filter by date, risk level, decision type
- Complete reasoning for regulatory compliance
- Export to CSV or JSON
- Statistics and charts

---

## 🚀 Quick Start

### Prerequisites

1. **FastAPI server must be running** on port 8000
   ```bash
   # In the main project directory
   python main.py
   ```

2. **Install dashboard dependencies**
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

### Start the Dashboard

```bash
streamlit run Home.py
```

The dashboard will open automatically in your browser at **http://localhost:8501**

---

## 📖 User Guide

### Analyzing a Task

1. Click **"Analyze Task"** on the home page
2. Fill in organization details (dropdowns and checkboxes)
3. Describe the compliance task
4. Click **"Analyze Task"** button
5. Get instant results:
   - ✅ **AUTONOMOUS** - Proceed independently
   - ⚠️ **REVIEW_REQUIRED** - Get approval first
   - 🚨 **ESCALATE** - Requires expert

### Generating a Compliance Calendar

1. Click **"Create Calendar"** on the home page
2. Enter organization name and select locations
3. Choose organization type and industry
4. Click **"Generate Calendar"**
5. View all compliance tasks with:
   - Deadlines and frequencies
   - Risk levels
   - Autonomy recommendations
   - Export options

### Viewing Audit Trail

1. Click **"View Audit Log"** on the home page
2. Use filters to narrow results:
   - Time period
   - Decision type
   - Risk level
3. Click on any record to see:
   - Complete reasoning
   - Risk factor breakdown
   - Recommendations
4. Export filtered results or complete trail

---

## 🎨 Dashboard vs API Docs

| Feature | Swagger Docs | Business Dashboard |
|---------|--------------|-------------------|
| **Audience** | Developers | Business users |
| **Interface** | Raw JSON | Forms & dropdowns |
| **Learning Curve** | High | None |
| **Results Display** | JSON | Tables & charts |
| **Export** | Manual | One-click |
| **Help Text** | Technical | Plain English |

**Before (Swagger):**
```json
{
  "entity": {
    "name": "string",
    "entity_type": "STARTUP",
    ...
  }
}
```

**After (Dashboard):**
```
Organization Name: [Text Input]
Organization Type: [Dropdown: Startup, Company, etc.]
```

---

## 🛠️ Troubleshooting

### Dashboard won't start
- **Error**: "Cannot connect to API"
- **Solution**: Make sure FastAPI server is running:
  ```bash
  cd ..
  python main.py
  ```

### Port already in use
- **Error**: "Port 8501 is already in use"
- **Solution**: Kill existing process or use different port:
  ```bash
  streamlit run Home.py --server.port 8502
  ```

### Missing dependencies
- **Error**: "Module not found"
- **Solution**: Install requirements:
  ```bash
  pip install -r requirements.txt
  ```

---

## 📦 Deployment Options

### Local Development
```bash
streamlit run Home.py
```

### Production Deployment

**Option 1: Streamlit Cloud** (Free)
1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect repository
4. Deploy!

**Option 2: Docker**
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "Home.py", "--server.port", "8501"]
```

**Option 3: AWS/GCP/Azure**
- Use any cloud provider's app hosting service
- Configure ports: 8501 (Streamlit), 8000 (FastAPI)

---

## 🔐 Authentication (Optional)

To add authentication, create a `.streamlit/config.toml` file:

```toml
[server]
enableCORS = false

[client]
showErrorDetails = false
```

Then add to your pages:

```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == "your_password":
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

---

## 📚 Additional Resources

- **Main Project README**: `../README.md`
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Docs**: https://docs.streamlit.io

---

## 🆘 Support

For issues or questions:
1. Check the help sections in each page (click ❓)
2. Review the main project README
3. Check API logs: `server.log` in project root

---

**Built with ❤️ using Streamlit and Python**

