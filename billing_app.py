import json
import os
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QFrame, QTabWidget, QHeaderView
)
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize, QDir
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import logging

# --- Logging Configuration ---
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Inventory File ---
INVENTORY_FILE_PATH = "inventory.json"

# --- Inventory Functions ---
def load_inventory():
    if os.path.exists(INVENTORY_FILE_PATH):
        try:
            with open(INVENTORY_FILE_PATH, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

def save_inventory(inventory):
    with open(INVENTORY_FILE_PATH, "w") as file:
        json.dump(inventory, indent=4)

def add_product(name, price, material_code):
    inventory = load_inventory()
    inventory.append({"name": name, "price": float(price), "material_code": material_code})
    save_inventory(inventory)
    return inventory

def update_product(index, name, price, material_code):
    inventory = load_inventory()
    if 0 <= index < len(inventory):
        inventory[index] = {"name": name, "price": float(price), "material_code": material_code}
        save_inventory(inventory)
    return inventory

def delete_product(index):
    inventory = load_inventory()
    if 0 <= index < len(inventory):
        del inventory[index]
        save_inventory(inventory)
    return inventory

# --- Dialogs ---
class AddOrEditProductDialog(QDialog):
    def __init__(self, parent=None, mode="Add", product=None):
        super().__init__(parent)
        self.setWindowTitle(f"{mode} Product")
        self.setMinimumSize(350, 250)
        self.mode = mode
        self.product = product
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.material_code_input = QLineEdit()

        if self.product:
            self.name_input.setText(self.product["name"])
            self.price_input.setText(str(self.product["price"]))
            self.material_code_input.setText(self.product["material_code"])

        name_label = QLabel("Product Name:")
        price_label = QLabel("Price:")
        material_code_label = QLabel("Material Code:")

        name_label.setFont(QFont("Segoe UI", 10))
        price_label.setFont(QFont("Segoe UI", 10))
        material_code_label.setFont(QFont("Segoe UI", 10))
        self.name_input.setFont(QFont("Segoe UI", 10))
        self.price_input.setFont(QFont("Segoe UI", 10))
        self.material_code_input.setFont(QFont("Segoe UI", 10))

        layout.addRow(name_label, self.name_input)
        layout.addRow(price_label, self.price_input)
        layout.addRow(material_code_label, self.material_code_input)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.save_button.setStyleSheet("padding: 8px 15px; border-radius: 5px; background-color: #5cb85c; color: white;")
        self.save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(QFont("Segoe UI", 10))
        cancel_button.setStyleSheet("padding: 8px 15px; border-radius: 5px;")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)

        layout.addItem(button_layout)
        self.setLayout(layout)

    def get_data(self):
        return self.name_input.text(), self.price_input.text(), self.material_code_input.text()

# --- Inventory Screen ---
class InventoryScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Price", "Material Code", "Actions"])
        self.table.setFont(QFont("Segoe UI", 10))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Product")
        add_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        add_button.setStyleSheet("padding: 10px 20px; border-radius: 5px; background-color: #007bff; color: white;")
        add_button.clicked.connect(self.add_product)
        next_button = QPushButton("Next ➡️ Billing")
        next_button.setFont(QFont("Segoe UI", 10))
        next_button.setStyleSheet("padding: 10px 20px; border-radius: 5px; background-color: #28a745; color: white;")
        next_button.clicked.connect(lambda: self.parent.setCurrentIndex(1))
        button_layout.addWidget(add_button)
        button_layout.addWidget(next_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.load_inventory()

    def load_inventory(self):
        self.table.setRowCount(0)
        self.inventory = load_inventory()
        for index, item in enumerate(self.inventory):
            self.table.insertRow(index)
            self.table.setItem(index, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(index, 1, QTableWidgetItem(f"₹{item['price']:.2f}"))
            self.table.setItem(index, 2, QTableWidgetItem(item["material_code"]))

            edit_btn = QPushButton()
            edit_btn.setIcon(QIcon(":/icons/edit.png"))  # Use a pen icon
            edit_btn.setIconSize(QSize(20, 20))
            edit_btn.setToolTip("Edit")
            edit_btn.setStyleSheet("padding: 5px; border-radius: 3px; background-color: #ffc107;")
            edit_btn.clicked.connect(lambda _, idx=index: self.edit_product(idx))

            del_btn = QPushButton()
            del_btn.setIcon(QIcon(":/icons/trash.png"))  # Use a trashcan icon
            del_btn.setIconSize(QSize(20, 20))
            del_btn.setToolTip("Delete")
            del_btn.setStyleSheet("padding: 5px; border-radius: 3px; background-color: #dc3545;")
            del_btn.clicked.connect(lambda _, idx=index: self.delete_product(idx))

            hbox = QHBoxLayout()
            hbox.addWidget(edit_btn)
            hbox.addWidget(del_btn)
            frame = QWidget()
            frame.setLayout(hbox)
            self.table.setCellWidget(index, 3, frame)

        if hasattr(self.parent, 'billing_tab'):
            self.parent.billing_tab.update_products()

    def add_product(self):
        dialog = AddOrEditProductDialog(self, "Add")
        if dialog.exec_():
            name, price, code = dialog.get_data()
            self.inventory = add_product(name, price, code)
            self.load_inventory()

    def edit_product(self, index):
        item = self.inventory[index]
        dialog = AddOrEditProductDialog(self, "Edit", item)
        if dialog.exec_():
            name, price, code = dialog.get_data()
            self.inventory = update_product(index, name, price, code)
            self.load_inventory()

    def delete_product(self, index):
        confirm = QMessageBox.question(self, "Confirm", "Are you sure you want to delete this product?",
                                            QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.inventory = delete_product(index)
            self.load_inventory()

# --- Billing Screen ---
class BillingScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.cart = []
        self.layout = QVBoxLayout()

        self.title = QLabel("Billing")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)

        input_layout = QHBoxLayout()
        self.product_combo = QComboBox()
        self.product_combo.setFont(QFont("Segoe UI", 10))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setFont(QFont("Segoe UI", 10))
        self.gst_combo = QComboBox()
        self.gst_combo.addItem("No GST", 0.0)
        self.gst_combo.addItem("GST 18%", 0.18)
        self.gst_combo.addItem("GST 28%", 0.28)
        self.gst_combo.setFont(QFont("Segoe UI", 10))
        self.add_button = QPushButton("Add to Cart")
        self.add_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.add_button.setStyleSheet("padding: 8px 15px; border-radius: 5px; background-color: #00c853; color: white;")
        self.add_button.clicked.connect(self.add_to_cart)
        input_layout.addWidget(QLabel("Product:"))
        input_layout.addWidget(self.product_combo)
        input_layout.addWidget(QLabel("Quantity:"))
        input_layout.addWidget(self.quantity_spin)
        input_layout.addWidget(QLabel("GST:"))
        input_layout.addWidget(self.gst_combo)
        input_layout.addWidget(self.add_button)
        self.layout.addLayout(input_layout)

        self.cart_table = QTableWidget(0, 5)  # Add one column for serial number
        self.cart_table.setHorizontalHeaderLabels(["Sr.No", "Product", "Qty", "Price", "Total"])
        self.cart_table.setFont(QFont("Segoe UI", 10))
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.cart_table)

        billed_to_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setFont(QFont("Segoe UI", 10))
        billed_to_layout.addWidget(QLabel("Billed To:"))
        billed_to_layout.addWidget(self.name_input)
        self.layout.addLayout(billed_to_layout)

        generate_button = QPushButton("Generate Bill")
        generate_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        generate_button.setStyleSheet("padding: 10px 20px; border-radius: 5px; background-color: #3f51b5; color: white;")
        generate_button.clicked.connect(self.generate_pdf)
        self.layout.addWidget(generate_button)

        back_button = QPushButton("⬅️ Inventory")
        back_button.setFont(QFont("Segoe UI", 10))
        back_button.setStyleSheet("padding: 8px 15px; border-radius: 5px;")
        back_button.clicked.connect(lambda: self.parent.setCurrentIndex(0))
        self.layout.addWidget(back_button)

        self.setLayout(self.layout)
        self.update_products()

    def update_products(self):
        self.product_combo.clear()
        self.products = load_inventory()
        for p in self.products:
            self.product_combo.addItem(f"{p['name']} (₹{p['price']:.2f})", p)

    def add_to_cart(self):
        index = self.product_combo.currentIndex()
        if index < 0:
            return
        product = self.products[index]
        qty = self.quantity_spin.value()
        gst_rate = self.gst_combo.currentData()
        price = product['price']
        total_without_gst = price * qty
        gst_amount = total_without_gst * gst_rate
        total_with_gst = total_without_gst + gst_amount
        self.cart.append((product, qty, price, gst_rate, total_with_gst))

        row = self.cart_table.rowCount()
        self.cart_table.insertRow(row)
        self.cart_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))  # Add serial number
        self.cart_table.setItem(row, 1, QTableWidgetItem(product['name']))
        self.cart_table.setItem(row, 2, QTableWidgetItem(str(qty)))
        self.cart_table.setItem(row, 3, QTableWidgetItem(f"₹{price:.2f}"))
        self.cart_table.setItem(row, 4, QTableWidgetItem(f"₹{total_with_gst:.2f}"))

    def generate_pdf(self):
        billed_to = self.name_input.text()
        if not billed_to:
            QMessageBox.warning(self, "Missing Name", "Please enter the name of the person being billed.")
            return

        import os
        import time
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        order_no = f"ORD{int(time.time())}"
        desktop = os.path.expanduser("~/Desktop")
        billings_folder = os.path.join(desktop, "globizz-app-billings")
        os.makedirs(billings_folder, exist_ok=True)
        filename = os.path.join(billings_folder, f"{order_no}.pdf")

        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.alignment = 1
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        bold_style = ParagraphStyle(name='Bold', parent=normal_style, fontName='Helvetica-Bold')

        # Header
        elements.append(Paragraph("Globizz Solutions", title_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Address: G.T.B. Nagar,Ludhiana - 141015 (Punjab)", normal_style))
        elements.append(Paragraph("Mail: sanjiv@globizzsolutions.com, globizzsolutions@gmail.com", normal_style))
        elements.append(Paragraph("Phone: 98728-71664, 9915700364, 0161-4100361", normal_style))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(f"Order No.: {order_no}", normal_style))
        elements.append(Paragraph(f"Billed To: {billed_to}", normal_style))
        elements.append(Paragraph(f"Date: {time.strftime('%d %B %Y')}", normal_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Product Table
        data = [["Sr.No", "Product", "Qty", "Price", "Total"]]
        net_total = 0

        for i, (product, qty, price, gst_rate, total) in enumerate(self.cart):
            data.append([
                str(i + 1),
                product['name'],
                str(qty),
                f"Rs {price:.2f}",
                f"Rs {total:.2f}"
            ])
            net_total += total

        product_table = Table(data, colWidths=[40, 240, 50, 80, 80])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(product_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Charges Calculations
        freight = round(net_total * 0.025, 2)
        gst_rate = self.cart[0][3] if self.cart else 0.18  # Default GST if cart is empty
        gst = round((net_total + freight) * gst_rate, 2)
        gross_total = net_total + freight + gst

        # Elegant Summary Table (Compact & Right-Aligned)
        summary_data = [
            ["Net Total", f"Rs {net_total:.2f}"],
            ["Freight (2.5%)", f"Rs {freight:.2f}"],
            [f"GST ({gst_rate * 100:.0f}%)", f"Rs {gst:.2f}"],
            ["Gross Total", f"Rs {gross_total:.2f}"]
        ]

        summary_table = Table(summary_data, colWidths=[150, 100])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('RIGHTPADDING', (1, 0), (1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))

        # Wrap in right-aligned layout
        summary_wrapper = Table([[Spacer(1, 0), summary_table]], colWidths=[350, 250])
        elements.append(summary_wrapper)
        elements.append(Spacer(1, 0.5 * inch))

        elements.append(Paragraph("Thank you for your business!", normal_style))
        doc.build(elements)

        QMessageBox.information(self, "Success", f"Bill generated and saved to: {filename}")

        # Clear cart UI
        self.cart = []
        self.cart_table.setRowCount(0)

# --- Main Application ---
class MainApp(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Globizz Billing & Inventory")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #fefefe;
                font-family: "Helvetica Neue", "Segoe UI", "San Francisco", sans-serif;
                font-size: 14px;
                color: #2e2e2e;
            }

            /* QLabel */
            QLabel {
                color: #2e2e2e;
                font-weight: 500;
            }

            /* QLineEdit */
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007aff; /* Mac accent blue */
            }

            /* QPushButton */
            QPushButton {
                background-color: #e0e0e0;
                color: #2e2e2e;
                border: 1px solid #c7c7c7;
                padding: 6px 14px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #d5d5d5;
            }
            QPushButton:pressed {
                background-color: #c2c2c2;
            }
            QPushButton:disabled {
                color: #aaaaaa;
                background-color: #f2f2f2;
                border-color: #e1e1e1;
            }

            /* QTableWidget */
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                gridline-color: #eaeaea;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #555;
                border: none;
                font-weight: 600;
                padding: 6px;
                border-bottom: 1px solid #dcdcdc;
            }

            /* QComboBox */
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #007aff;
            }

            /* QScrollBar (vertical) */
            QScrollBar:vertical {
                background: #f2f2f2;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c4c4c4;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            /* Misc */
            QGroupBox {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                color: #444;
            }
        """)
        self.inventory_tab = InventoryScreen(self)
        self.billing_tab = BillingScreen(self)
        self.addTab(self.inventory_tab, "🧾 Inventory")
        self.addTab(self.billing_tab, "💰 Billing")

# --- Entry Point ---
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Load icons from the application's resource path
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
    QDir.addSearchPath("icons", icon_path)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
