import re
from PIL import Image, ImageTk
import pytesseract
import qrcode
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import webbrowser
import requests
import json
import os
from dotenv import load_dotenv
import speech_recognition as sr
import threading 
import time
from queue import Queue

# Load environment variables
load_dotenv()

# Initialize global variables with additional categories
categories_data = {
    "Food": [],
    "Health": [],
    "Monthly Bills": [],
    "EMI": [],
    "Shopping": [],
    "Entertainment": [],
    "Education": [],
    "Insurance": [],
    "Travel": [],
    "Office Supplies": [],
    "Utilities": [],
    "Maintenance": [],
    "Marketing": [],
    "Software": [],
    "Hardware": []
}

# Path to the Tesseract executable (change this if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Global variable for selected image path
selected_image_path = None

# Voice recognition variables
voice_queue = Queue()
is_listening = False
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# CEO Dashboard data
ceo_dashboard_data = {
    "monthly_budget": 100000,  # Default budget
    "department_spending": {},
    "alerts": [],
    "savings_goals": {}
}

def initialize_ceo_dashboard():
    """Initialize default CEO dashboard data"""
    ceo_dashboard_data["department_spending"] = {
        "HR": {"budget": 20000, "spent": 0},
        "IT": {"budget": 30000, "spent": 0},
        "Marketing": {"budget": 25000, "spent": 0},
        "Operations": {"budget": 25000, "spent": 0}
    }
    ceo_dashboard_data["savings_goals"] = {
        "Q1": {"target": 50000, "saved": 0},
        "Q2": {"target": 60000, "saved": 0},
        "Q3": {"target": 70000, "saved": 0},
        "Q4": {"target": 80000, "saved": 0}
    }

def ocr_and_filter_total(image_path, category_name):
    try:
        # Perform OCR on the image
        text = pytesseract.image_to_string(Image.open(image_path))
        
        # Filter sentences containing the keyword "TOTAL"
        sentences = text.split('\n')
        total_sentences = [sentence for sentence in sentences if 'TOTAL' in sentence.upper()]
        
        # Extract and store the numerical part of the filtered sentences
        total_amounts = []
        for sentence in total_sentences:
            # Use regular expression to extract numerical part (including commas)
            total_amount = re.search(r'[\d,]+\.*\d*', sentence.replace(',', ''))
            if total_amount:
                total_amounts.append(float(total_amount.group()))

        if not total_amounts:
            messagebox.showerror("Error", "No total amount found in the image.")
            return False

        max_amount = max(total_amounts)
        categories_data[category_name].append(max_amount)
        
        # Update CEO dashboard
        update_ceo_dashboard(category_name, max_amount)
        
        # Add timestamp to the expense
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        messagebox.showinfo("Success", f"Bill of ₹{max_amount:.2f} added successfully to {category_name} at {timestamp}")
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to process image: {str(e)}")
        return False

def update_ceo_dashboard(category, amount):
    """Update CEO dashboard data when new expenses are added"""
    # Update department spending (simplified mapping)
    department = "Operations"  # Default department
    if category in ["Software", "Hardware", "Office Supplies"]:
        department = "IT"
    elif category in ["Marketing"]:
        department = "Marketing"
    elif category in ["Health", "Insurance"]:
        department = "HR"

    if department in ceo_dashboard_data["department_spending"]:
        ceo_dashboard_data["department_spending"][department]["spent"] += amount
    
    # Check for budget alerts
    check_budget_alerts()
    
    # Update savings (simplified - assumes savings is budget minus spent)
    quarter = "Q" + str((datetime.now().month - 1) // 3 + 1)
    if quarter in ceo_dashboard_data["savings_goals"]:
        total_spent = sum(sum(expenses) for expenses in categories_data.values())
        ceo_dashboard_data["savings_goals"][quarter]["saved"] = ceo_dashboard_data["monthly_budget"] - total_spent

def check_budget_alerts():
    """Check for budget overruns and add alerts"""
    ceo_dashboard_data["alerts"] = []
    for dept, data in ceo_dashboard_data["department_spending"].items():
        if data["spent"] > data["budget"]:
            overage = data["spent"] - data["budget"]
            ceo_dashboard_data["alerts"].append(
                f"Budget overrun in {dept}: ₹{overage:.2f} over budget"
            )
    
    # Check overall budget
    total_spent = sum(sum(expenses) for expenses in categories_data.values())
    if total_spent > ceo_dashboard_data["monthly_budget"]:
        overage = total_spent - ceo_dashboard_data["monthly_budget"]
        ceo_dashboard_data["alerts"].append(
            f"Company-wide budget overrun: ₹{overage:.2f} over monthly budget"
        )

def calculate_totals():
    return {category: sum(expenses) for category, expenses in categories_data.items()}

def generate_qr_code():
    totals = calculate_totals()
    GT = sum(totals.values())
    qr_data = "=== Expense Summary ===\n"
    qr_data += "\n".join([f"{category}: ₹{amount:.2f}" for category, amount in totals.items()])
    qr_data += f"\n\nGrand Total: ₹{GT:.2f}"
    qr_data += f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((250, 250), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img), qr_data

def show_pie_chart():
    totals = calculate_totals()
    categories = list(totals.keys())
    amounts = list(totals.values())
    
    # Create small slices for zero values so all categories appear
    amounts = [v if v > 0 else 0.1 for v in amounts]
    
    # Create a colorful palette
    colors = plt.cm.tab20c(range(len(categories)))
    
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        amounts, 
        labels=categories, 
        autopct=lambda p: f'{p:.1f}%\n(₹{p * sum(amounts)/100:.2f})' if p > 1 else '',
        startangle=140,
        colors=colors,
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
    )
    
    # Hide labels and percentages for zero (actually 0.1) values
    for i, amount in enumerate(totals.values()):
        if amount == 0:
            texts[i].set_visible(False)
            autotexts[i].set_visible(False)
    
    ax.axis('equal')
    ax.set_title('Company Expenditure Distribution', pad=20, fontweight='bold')
    plt.tight_layout()
    
    # Create a new window for the chart
    chart_window = tk.Toplevel()
    chart_window.title("Expenditure Analysis")
    
    # Add export button
    def export_chart():
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=f"expense_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if filename:
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Chart exported as {filename}")
    
    export_btn = tk.Button(chart_window, text="Export Chart", command=export_chart)
    export_btn.pack(pady=5)
    
    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack()

def show_summary():
    totals = calculate_totals()
    GT = sum(totals.values())
    
    summary_window = tk.Toplevel()
    summary_window.title("Expenditure Summary Report")
    summary_window.geometry("600x700")
    
    # Main frame with scrollbar
    main_frame = tk.Frame(summary_window)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Header
    header_frame = tk.Frame(scrollable_frame)
    header_frame.pack(pady=10, fill=tk.X)
    
    tk.Label(
        header_frame, 
        text="COMPANY EXPENSE SUMMARY", 
        font=('Helvetica', 14, 'bold'),
        fg='#2c3e50'
    ).pack()
    
    tk.Label(
        header_frame, 
        text=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        font=('Helvetica', 9),
        fg='#7f8c8d'
    ).pack()
    
    # Summary table
    table_frame = tk.Frame(scrollable_frame)
    table_frame.pack(pady=10, padx=10, fill=tk.X)
    
    # Table header
    tk.Label(
        table_frame, 
        text="Category", 
        font=('Helvetica', 10, 'bold'),
        width=20,
        anchor='w',
        borderwidth=1,
        relief='solid'
    ).grid(row=0, column=0, sticky='ew')
    
    tk.Label(
        table_frame, 
        text="Amount (₹)", 
        font=('Helvetica', 10, 'bold'),
        width=15,
        anchor='e',
        borderwidth=1,
        relief='solid'
    ).grid(row=0, column=1, sticky='ew')
    
    # Table rows
    for i, (category, amount) in enumerate(totals.items(), start=1):
        tk.Label(
            table_frame, 
            text=category,
            anchor='w',
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=0, sticky='ew')
        
        tk.Label(
            table_frame, 
            text=f"{amount:.2f}",
            anchor='e',
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=1, sticky='ew')
    
    # Grand Total
    tk.Label(
        table_frame, 
        text="GRAND TOTAL", 
        font=('Helvetica', 10, 'bold'),
        anchor='w',
        borderwidth=1,
        relief='solid'
    ).grid(row=len(totals)+1, column=0, sticky='ew')
    
    tk.Label(
        table_frame, 
        text=f"{GT:.2f}", 
        font=('Helvetica', 10, 'bold'),
        anchor='e',
        borderwidth=1,
        relief='solid'
    ).grid(row=len(totals)+1, column=1, sticky='ew')
    
    # QR Code
    qr_frame = tk.Frame(scrollable_frame)
    qr_frame.pack(pady=20)
    
    qr_img, qr_data = generate_qr_code()
    qr_label = tk.Label(qr_frame, image=qr_img)
    qr_label.image = qr_img
    qr_label.pack()
    
    tk.Label(
        qr_frame, 
        text="Scan for expense summary", 
        font=('Helvetica', 8),
        fg='#7f8c8d'
    ).pack()
    
    # Buttons
    btn_frame = tk.Frame(scrollable_frame)
    btn_frame.pack(pady=20)
    
    tk.Button(
        btn_frame, 
        text="Show Pie Chart", 
        command=show_pie_chart,
        bg='#3498db',
        fg='white',
        padx=10
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame, 
        text="Export Data", 
        command=lambda: export_data(totals),
        bg='#2ecc71',
        fg='white',
        padx=10
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame, 
        text="Get AI Insights", 
        command=lambda: get_ai_insights(totals),
        bg='#9b59b6',
        fg='white',
        padx=10
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame, 
        text="Close", 
        command=summary_window.destroy,
        bg='#e74c3c',
        fg='white',
        padx=10
    ).pack(side=tk.LEFT, padx=5)

def export_data(totals):
    filename = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile=f"expense_report_{datetime.now().strftime('%Y%m%d')}.txt"
    )
    
    if filename:
        try:
            if filename.endswith('.csv'):
                # Export as CSV with UTF-8 encoding
                with open(filename, 'w', encoding='utf-8') as f:  # Add encoding here
                    f.write("Category,Amount (₹)\n")
                    for category, amount in totals.items():
                        f.write(f"{category},{amount:.2f}\n")
                    GT = sum(totals.values())
                    f.write(f"GRAND TOTAL,{GT:.2f}\n")
            else:
                # Export as text with UTF-8 encoding
                with open(filename, 'w', encoding='utf-8') as f:  # Add encoding here
                    f.write("=== COMPANY EXPENSE REPORT ===\n\n")
                    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for category, amount in totals.items():
                        f.write(f"{category:<20}: ₹{amount:>10.2f}\n")  # ₹ symbol will work now
                    
                    GT = sum(totals.values())
                    f.write("\n")
                    f.write(f"{'GRAND TOTAL':<20}: ₹{GT:>10.2f}\n")
            
            messagebox.showinfo("Success", f"Report exported successfully to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export file: {str(e)}")
            
def upload_bill():
    global selected_image_path
    selected_image_path = None
    
    upload_window = tk.Toplevel()
    upload_window.title("Upload Expense Bill")
    upload_window.geometry("400x500")
    
    # Category selection
    tk.Label(
        upload_window, 
        text="Select Expense Category:", 
        font=('Helvetica', 11, 'bold'),
        pady=10
    ).pack()
    
    category_var = tk.StringVar(value="")
    
    # Create a scrollable frame for categories
    canvas = tk.Canvas(upload_window)
    scrollbar = ttk.Scrollbar(upload_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Add category radio buttons
    for i, category in enumerate(categories_data.keys()):
        tk.Radiobutton(
            scrollable_frame, 
            text=category,
            variable=category_var,
            value=category,
            font=('Helvetica', 10),
            padx=10,
            pady=5
        ).pack(anchor='w')
    
    # Image selection section
    tk.Label(
        upload_window,
        text="\nSelect Bill Image:",
        font=('Helvetica', 11, 'bold'),
        pady=10
    ).pack()
    
    def on_image_select():
        category = category_var.get()
        if not category:
            messagebox.showerror("Error", "Please select a category first")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Bill Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            # Show preview of selected image
            try:
                img = Image.open(file_path)
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                
                preview_label.config(image=photo)
                preview_label.image = photo
                file_label.config(text=file_path.split('/')[-1])
                
                # Add confirm button
                confirm_btn.config(state=tk.NORMAL)
                global selected_image_path
                selected_image_path = file_path
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")
    
    # Image preview and file info
    preview_frame = tk.Frame(upload_window)
    preview_frame.pack(pady=10)
    
    preview_label = tk.Label(preview_frame)
    preview_label.pack()
    
    file_label = tk.Label(preview_frame, text="No image selected", fg='gray')
    file_label.pack()
    
    # Manual entry option
    manual_frame = tk.Frame(upload_window)
    manual_frame.pack(pady=10)
    
    tk.Label(
        manual_frame,
        text="Or enter amount manually:",
        font=('Helvetica', 9)
    ).pack()
    
    manual_amount = tk.StringVar()
    tk.Entry(
        manual_frame,
        textvariable=manual_amount,
        width=15,
        font=('Helvetica', 10)
    ).pack()
    
    def add_manual_amount():
        category = category_var.get()
        if not category:
            messagebox.showerror("Error", "Please select a category first")
            return
        
        try:
            amount = float(manual_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            categories_data[category].append(amount)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            messagebox.showinfo("Success", f"Manual entry of ₹{amount:.2f} added successfully to {category} at {timestamp}")
            
            # Update CEO dashboard
            update_ceo_dashboard(category, amount)
            
            upload_window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {str(e)}")
    
    # Buttons frame
    btn_frame = tk.Frame(upload_window)
    btn_frame.pack(pady=20)
    
    tk.Button(
        btn_frame,
        text="Select Image",
        command=on_image_select,
        bg='#3498db',
        fg='white',
        padx=15
    ).pack(side=tk.LEFT, padx=5)
    
    confirm_btn = tk.Button(
        btn_frame,
        text="Upload Bill",
        state=tk.DISABLED,
        bg='#2ecc71',
        fg='white',
        padx=15,
        command=lambda: process_upload(category_var.get(), upload_window)
    )
    confirm_btn.pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="Add Manually",
        command=add_manual_amount,
        bg='#f39c12',
        fg='white',
        padx=15
    ).pack(side=tk.LEFT, padx=5)

def process_upload(category, window):
    global selected_image_path
    if selected_image_path and category:
        if ocr_and_filter_total(selected_image_path, category):
            window.destroy()
    selected_image_path = None

def get_ai_insights(expense_data):
    """Get AI-powered insights using Groq API"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            messagebox.showerror("Error", "Groq API key not found in environment variables")
            return
        
        # Prepare the prompt
        prompt = f"""Analyze this company expense data and provide insights and recommendations:
        
        Expense Breakdown:
        {json.dumps(expense_data, indent=2)}
        
        Total Expenses: ₹{sum(expense_data.values()):.2f}
        
        Please provide:
        1. Key observations about spending patterns
        2. Potential areas for cost optimization
        3. Recommendations for budget allocation
        4. Any unusual spending patterns to investigate
        
        Respond in clear, actionable bullet points suitable for a business manager."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.groq.com/v1/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        insights = response.json()["choices"][0]["text"]
        
        # Display insights in a new window
        insights_window = tk.Toplevel()
        insights_window.title("AI-Powered Expense Insights")
        insights_window.geometry("700x500")
        
        # Header
        tk.Label(
            insights_window,
            text="AI Expense Insights",
            font=('Helvetica', 14, 'bold'),
            pady=10
        ).pack()
        
        # Text widget for scrollable content
        text_frame = tk.Frame(insights_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        insights_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=('Helvetica', 10),
            padx=10,
            pady=10
        )
        insights_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=insights_text.yview)
        
        # Insert the insights
        insights_text.insert(tk.END, insights)
        insights_text.config(state=tk.DISABLED)  # Make it read-only
        
        # Close button
        tk.Button(
            insights_window,
            text="Close",
            command=insights_window.destroy,
            bg='#e74c3c',
            fg='white',
            padx=15
        ).pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("API Error", f"Failed to get AI insights: {str(e)}")

def show_help():
    help_window = tk.Toplevel()
    help_window.title("Help Guide")
    help_window.geometry("500x400")
    
    tk.Label(
        help_window,
        text="Expense Tracker User Guide",
        font=('Helvetica', 14, 'bold'),
        pady=10
    ).pack()
    
    help_text = """1. Upload Bill:
   - Select a category
   - Choose an image of your bill
   - The system will extract the total amount
   - Or enter the amount manually

2. View Summary:
   - See all expenses by category
   - View grand total
   - Generate QR code for sharing
   - Get AI-powered insights

3. Pie Chart:
   - Visual representation of expenses
   - Shows percentage distribution

4. Voice Commands:
   - Click the microphone button
   - Say commands like "Add 500 for food"
   - Or "Show me the pie chart"

5. CEO Dashboard:
   - View department budgets
   - Check savings goals
   - See alerts and notifications"""
    
    tk.Label(
        help_window,
        text=help_text,
        font=('Helvetica', 10),
        justify='left',
        padx=20,
        pady=10
    ).pack()
    
    tk.Button(
        help_window,
        text="Close",
        command=help_window.destroy,
        bg='#e74c3c',
        fg='white'
    ).pack(pady=10)

def show_ceo_dashboard():
    dashboard_window = tk.Toplevel()
    dashboard_window.title("CEO Dashboard")
    dashboard_window.geometry("800x600")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(dashboard_window)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Overview Tab
    overview_frame = ttk.Frame(notebook)
    notebook.add(overview_frame, text="Overview")
    
    # Budget Summary
    tk.Label(
        overview_frame,
        text="Budget Overview",
        font=('Helvetica', 12, 'bold'),
        pady=10
    ).pack()
    
    # Current month spending
    total_spent = sum(sum(expenses) for expenses in categories_data.values())
    budget_percentage = (total_spent / ceo_dashboard_data["monthly_budget"]) * 100
    
    budget_frame = tk.Frame(overview_frame)
    budget_frame.pack(pady=10, padx=20, fill=tk.X)
    
    tk.Label(
        budget_frame,
        text=f"Monthly Budget: ₹{ceo_dashboard_data['monthly_budget']:,.2f}",
        font=('Helvetica', 10)
    ).pack(anchor='w')
    
    tk.Label(
        budget_frame,
        text=f"Total Spent: ₹{total_spent:,.2f} ({budget_percentage:.1f}% of budget)",
        font=('Helvetica', 10)
    ).pack(anchor='w')
    
    # Progress bar
    progress = ttk.Progressbar(
        budget_frame,
        orient='horizontal',
        length=300,
        mode='determinate',
        maximum=100,
        value=min(budget_percentage, 100)
    )
    progress.pack(pady=5)
    
    # Alerts Section
    tk.Label(
        overview_frame,
        text="Alerts & Notifications",
        font=('Helvetica', 12, 'bold'),
        pady=10
    ).pack()
    
    alerts_frame = tk.Frame(overview_frame)
    alerts_frame.pack(pady=10, padx=20, fill=tk.X)
    
    if ceo_dashboard_data["alerts"]:
        for alert in ceo_dashboard_data["alerts"]:
            tk.Label(
                alerts_frame,
                text=f"⚠️ {alert}",
                font=('Helvetica', 10),
                fg='red',
                anchor='w'
            ).pack(fill=tk.X, pady=2)
    else:
        tk.Label(
            alerts_frame,
            text="No alerts at this time",
            font=('Helvetica', 10),
            fg='green'
        ).pack()
    
    # Department Spending Tab
    dept_frame = ttk.Frame(notebook)
    notebook.add(dept_frame, text="Departments")
    
    # Department spending table
    tk.Label(
        dept_frame,
        text="Department Spending",
        font=('Helvetica', 12, 'bold'),
        pady=10
    ).pack()
    
    table_frame = tk.Frame(dept_frame)
    table_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    # Table headers
    tk.Label(
        table_frame,
        text="Department",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=20
    ).grid(row=0, column=0, sticky='ew')
    
    tk.Label(
        table_frame,
        text="Budget",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=1, sticky='ew')
    
    tk.Label(
        table_frame,
        text="Spent",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=2, sticky='ew')
    
    tk.Label(
        table_frame,
        text="Remaining",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=3, sticky='ew')
    
    # Department rows
    for i, (dept, data) in enumerate(ceo_dashboard_data["department_spending"].items(), start=1):
        remaining = data["budget"] - data["spent"]
        
        tk.Label(
            table_frame,
            text=dept,
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=0, sticky='ew')
        
        tk.Label(
            table_frame,
            text=f"₹{data['budget']:,.2f}",
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=1, sticky='ew')
        
        tk.Label(
            table_frame,
            text=f"₹{data['spent']:,.2f}",
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=2, sticky='ew')
        
        tk.Label(
            table_frame,
            text=f"₹{remaining:,.2f}",
            borderwidth=1,
            relief='solid',
            fg='green' if remaining >= 0 else 'red'
        ).grid(row=i, column=3, sticky='ew')
    
    # Savings Goals Tab
    savings_frame = ttk.Frame(notebook)
    notebook.add(savings_frame, text="Savings Goals")
    
    tk.Label(
        savings_frame,
        text="Quarterly Savings Goals",
        font=('Helvetica', 12, 'bold'),
        pady=10
    ).pack()
    
    # Savings goals table
    savings_table = tk.Frame(savings_frame)
    savings_table.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    # Table headers
    tk.Label(
        savings_table,
        text="Quarter",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=0, sticky='ew')
    
    tk.Label(
        savings_table,
        text="Target",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=1, sticky='ew')
    
    tk.Label(
        savings_table,
        text="Saved",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=15
    ).grid(row=0, column=2, sticky='ew')
    
    tk.Label(
        savings_table,
        text="Progress",
        font=('Helvetica', 10, 'bold'),
        borderwidth=1,
        relief='solid',
        width=20
    ).grid(row=0, column=3, sticky='ew')
    
    # Savings rows
    for i, (quarter, data) in enumerate(ceo_dashboard_data["savings_goals"].items(), start=1):
        progress = (data["saved"] / data["target"]) * 100 if data["target"] > 0 else 0
        
        tk.Label(
            savings_table,
            text=quarter,
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=0, sticky='ew')
        
        tk.Label(
            savings_table,
            text=f"₹{data['target']:,.2f}",
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=1, sticky='ew')
        
        tk.Label(
            savings_table,
            text=f"₹{data['saved']:,.2f}",
            borderwidth=1,
            relief='solid'
        ).grid(row=i, column=2, sticky='ew')
        
        # Progress bar in a frame
        progress_frame = tk.Frame(savings_table)
        progress_frame.grid(row=i, column=3, sticky='ew')
        
        ttk.Progressbar(
            progress_frame,
            orient='horizontal',
            length=150,
            mode='determinate',
            maximum=100,
            value=progress
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            progress_frame,
            text=f"{progress:.1f}%",
            width=5
        ).pack(side=tk.LEFT)
    
    # Close button
    tk.Button(
        dashboard_window,
        text="Close Dashboard",
        command=dashboard_window.destroy,
        bg='#e74c3c',
        fg='white',
        padx=15
    ).pack(pady=10)

def process_voice_command(command):
    """Process voice commands and perform actions"""
    command = command.lower()
    
    # Add expense pattern: "add [amount] for [category]"
    add_pattern = r"add (\d+) for (\w+)"
    match = re.search(add_pattern, command)
    if match:
        amount = float(match.group(1))
        category = match.group(2).capitalize()
        
        # Find the best matching category
        matched_category = None
        for cat in categories_data.keys():
            if cat.lower().startswith(category.lower()):
                matched_category = cat
                break
        
        if matched_category:
            categories_data[matched_category].append(amount)
            update_ceo_dashboard(matched_category, amount)
            messagebox.showinfo("Success", f"Added ₹{amount:.2f} to {matched_category}")
        else:
            messagebox.showerror("Error", f"Category '{category}' not found")
        return
    
    # Other commands
    if "show pie chart" in command:
        show_pie_chart()
    elif "show summary" in command or "show report" in command:
        show_summary()
    elif "show dashboard" in command or "ceo dashboard" in command:
        show_ceo_dashboard()
    elif "help" in command:
        show_help()
    else:
        messagebox.showinfo("Voice Command", f"Command not recognized: {command}")

def listen_for_commands():
    """Background thread that listens for voice commands"""
    global is_listening
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        while is_listening:
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                command = recognizer.recognize_google(audio)
                voice_queue.put(command)
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"Voice recognition error: {e}")

def toggle_voice_recognition():
    """Toggle voice recognition on/off"""
    global is_listening
    
    if not is_listening:
        is_listening = True
        threading.Thread(target=listen_for_commands, daemon=True).start()
        voice_btn.config(text="🎙️ Listening...", bg='red', fg='white')
        messagebox.showinfo("Voice Control", "Voice recognition activated. Say commands like 'Add 500 for food'")
    else:
        is_listening = False
        voice_btn.config(text="🎤 Voice Control", bg='#3498db', fg='white')
        messagebox.showinfo("Voice Control", "Voice recognition deactivated")

def check_voice_queue():
    """Check the voice command queue periodically"""
    while not voice_queue.empty():
        command = voice_queue.get()
        process_voice_command(command)
    root.after(100, check_voice_queue)

def main_window():
    global root, voice_btn
    
    root = tk.Tk()
    root.title("Company Expense Tracker")
    root.geometry("500x600")  # Increased height for additional button
    root.configure(bg='#f5f6fa')
    
    # Initialize CEO dashboard data
    initialize_ceo_dashboard()
    
    # Header
    header_frame = tk.Frame(root, bg='#2c3e50')
    header_frame.pack(fill=tk.X)
    
    tk.Label(
        header_frame,
        text="COMPANY EXPENSE TRACKER",
        font=('Helvetica', 18, 'bold'),
        fg='white',
        bg='#2c3e50',
        pady=15
    ).pack()
    
    # Main buttons
    button_frame = tk.Frame(root, bg='#f5f6fa')
    button_frame.pack(pady=20)
    
    button_style = {
        'font': ('Helvetica', 12),
        'width': 20,
        'pady': 10,
        'bd': 0,
        'highlightthickness': 0
    }
    
    tk.Button(
        button_frame,
        text="📄 Upload New Bill",
        command=upload_bill,
        bg='#3498db',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    tk.Button(
        button_frame,
        text="📊 View Expense Summary",
        command=show_summary,
        bg='#2ecc71',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    tk.Button(
        button_frame,
        text="📈 Show Pie Chart",
        command=show_pie_chart,
        bg='#9b59b6',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    tk.Button(
        button_frame,
        text="👔 CEO Dashboard",
        command=show_ceo_dashboard,
        bg='#34495e',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    tk.Button(
        button_frame,
        text="🤖 Get AI Insights",
        command=lambda: get_ai_insights(calculate_totals()),
        bg='#1abc9c',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    voice_btn = tk.Button(
        button_frame,
        text="🎤 Voice Control",
        command=toggle_voice_recognition,
        bg='#3498db',
        fg='white',
        **button_style
    )
    voice_btn.pack(pady=8)
    
    tk.Button(
        button_frame,
        text="❓ Help Guide",
        command=show_help,
        bg='#f39c12',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    tk.Button(
        button_frame,
        text="🚪 Exit",
        command=root.destroy,
        bg='#e74c3c',
        fg='white',
        **button_style
    ).pack(pady=8)
    
    # Footer
    footer_frame = tk.Frame(root, bg='#34495e')
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    tk.Label(
        footer_frame,
        text="© 2023 Company Expense Tracker | For Internal Use Only",
        font=('Helvetica', 8),
        fg='white',
        bg='#34495e',
        pady=5
    ).pack()
    
    # Start checking for voice commands
    root.after(100, check_voice_queue)
    
    root.mainloop()

if __name__ == "__main__":
    main_window()