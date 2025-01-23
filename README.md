# Invoice-Management-System
This system is a desktop invoice management tool built with Python Tkinter and SQLite. It supports CRUD operations for invoices, PDF attachment management, automatic backups, reimbursement status tracking, and more. Designed for individuals or small teams to manage daily reimbursement tasks.

## Key Features

- **Core Functionality**  
  ✅ Invoice Management (content, amount, platform, type, notes)  
  ✅ PDF Attachment Linking & Quick View  
  ✅ Reimbursement Status Toggle (Reimbursed/Unreimbursed)  
  ✅ Data Search & Sorting (multi-column sorting, fuzzy keyword search)  
  ✅ Weekly Automatic Backups (retains latest 5 backups)  
  ✅ Manual Backup Trigger  

- **UI/UX Highlights**  
  🖥️ Responsive GUI (supports full-screen mode)  
  📊 Real-Time Statistics Panel (total count, total amount)  
  🛠️ Data Validation & Error Handling  
  🖨️ Cross-Platform PDF Viewer Integration (Windows/Linux/macOS)

---

## Requirements

- **Supported OS**  
  Windows / Linux / macOS

- **Dependencies**  
  ```bash
  # Install required packages
  pip install tkcalendar

## File Structure

```bash
├── main.py                # Main entry
├── components/            # UI modules
│   ├── detail_panel.py    # Detail panel
│   ├── invoice_dialog.py  # Add/Edit dialog
│   └── treeview.py        # Table view component
├── utils/
│   └── backup.py          # Backup module
├── invoices.db            # Database (auto-generated)
├── invoices_pdf/          # PDF storage (auto-generated)
└── backups/               # Backups (auto-generated)
