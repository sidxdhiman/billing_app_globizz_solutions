import json
import os
import time
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
import logging

# --- Logging Configuration ---
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')

# --- JSON File Functions ---
INVENTORY_FILE_PATH = "inventory.json"

def load_inventory_from_json():
    logging.info("Loading inventory from JSON file.")
    if os.path.exists(INVENTORY_FILE_PATH):
        try:
            with open(INVENTORY_FILE_PATH, "r") as file:
                inventory = json.load(file)
                logging.info(f"Inventory loaded successfully: {inventory}")
                return inventory
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {INVENTORY_FILE_PATH}: {e}")
            return []
    else:
        logging.info(f"Inventory file {INVENTORY_FILE_PATH} not found. Returning empty inventory.")
        return []

def save_inventory_to_json(inventory):
    logging.info(f"Saving inventory to JSON file: {inventory}")
    try:
        with open(INVENTORY_FILE_PATH, "w") as file:
            json.dump(inventory, file, indent=4)
        logging.info("Inventory saved successfully.")
    except IOError as e:
        logging.error(f"Error writing to {INVENTORY_FILE_PATH}: {e}")

def fetch_inventory():
    logging.info("Fetching inventory.")
    try:
        with open("inventory.json", "r") as file:
            items = json.load(file)
        inventory_data = [(item["name"], float(item["price"]), item["material_code"]) for item in items]
        logging.info(f"Inventory fetched: {inventory_data}")
        return inventory_data
    except FileNotFoundError:
        logging.warning("Inventory file not found.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding inventory JSON: {e}")
        return []

def add_product(name, price, material_code):
    logging.info(f"Adding product: Name='{name}', Price='{price}', Material Code='{material_code}'")
    inventory = load_inventory_from_json()
    inventory.append({"name": name, "price": price, "material_code": material_code})
    save_inventory_to_json(inventory)
    logging.info("Product added successfully.")

# --- Dialogs ---
class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Product")
        self.setMinimumSize(300, 200)
        self.init_ui()
        logging.info("AddProductDialog initialized.")

    def init_ui(self):
        logging.info("Initializing AddProductDialog UI.")
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.material_code_input = QLineEdit()

        layout.addRow("Product Name:", self.name_input)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Material Code:", self.material_code_input)

        self.add_button = QPushButton("Add Product")
        self.add_button.clicked.connect(self.add_product)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        logging.info("AddProductDialog UI initialized.")

    def add_product(self):
        logging.info("Add product button clicked in AddProductDialog.")
        name = self.name_input.text()
        price_text = self.price_input.text()
        material_code = self.material_code_input.text()
        try:
            price = float(price_text)
            add_product(name, price, material_code)
            self.accept()
            logging.info(f"Product '{name}' with price {price} and code '{material_code}' added.")
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid number for the price.")
            logging.warning(f"Invalid price entered: '{price_text}'.")

# --- Main Billing App ---
class BillingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Globizz Solutions - Billing App")
        self.setMinimumSize(750, 600)
        self.cart = []
        self.inventory = fetch_inventory()
        self.init_ui()
        logging.info("BillingApp initialized.")

    def init_ui(self):
        logging.info("Initializing BillingApp UI.")
        layout = QVBoxLayout()

        title = QLabel("Globizz Solutions Billing")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        # Product + Quantity + GST Layout
        hbox = QHBoxLayout()

        self.item_combo = QComboBox()
        self.update_inventory_combobox()
        self.item_combo.setFixedWidth(200)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedWidth(80)

        self.gst_combo = QComboBox()
        self.gst_combo.addItems(["18%", "28%"])
        self.gst_combo.setFixedWidth(80)

        self.add_button = QPushButton("Add Item")
        self.add_button.clicked.connect(self.add_to_cart)
        self.add_button.setFixedWidth(120)

        hbox.addWidget(QLabel("Item:"))
        hbox.addWidget(self.item_combo)
        hbox.addWidget(QLabel("Qty:"))
        hbox.addWidget(self.qty_spin)
        hbox.addWidget(QLabel("GST:"))
        hbox.addWidget(self.gst_combo)
        hbox.addWidget(self.add_button)

        layout.addLayout(hbox)

        # Add Product Button
        self.add_product_button = QPushButton("➕ Add New Product")
        self.add_product_button.clicked.connect(self.open_add_product_dialog)
        layout.addWidget(self.add_product_button)

        # Cart Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Item", "Qty", "Price", "GST%", "Total"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Bottom Layout
        bottom_hbox = QHBoxLayout()
        self.total_label = QLabel("Total: ₹0")
        self.total_label.setFont(QFont("Arial", 14, QFont.Bold))
        bottom_hbox.addWidget(self.total_label)

        self.bill_button = QPushButton("Generate Bill")
        self.bill_button.setStyleSheet("background-color: green; color: white; font-size: 14px;")
        self.bill_button.clicked.connect(self.generate_bill)
        bottom_hbox.addWidget(self.bill_button)

        layout.addLayout(bottom_hbox)
        self.setLayout(layout)
        logging.info("BillingApp UI initialized.")

    def update_inventory_combobox(self):
        logging.info("Updating inventory combobox.")
        self.item_combo.clear()
        for name, price, material_code in self.inventory:
            self.item_combo.addItem(f"{name} ({material_code}) - ₹{price}", (name, price, material_code))
        logging.info("Inventory combobox updated.")

    def add_to_cart(self):
        logging.info("Add item to cart button clicked.")
        idx = self.item_combo.currentIndex()
        item_info = self.item_combo.itemData(idx)
        if item_info:
            item_name, price, material_code = item_info
            qty = self.qty_spin.value()
            gst_rate_text = self.gst_combo.currentText().replace("%", "")
            try:
                gst_rate = int(gst_rate_text)
                price = float(price)
                price_with_gst = price + (price * gst_rate / 100)
                total = price_with_gst * qty

                self.cart.append((item_name, qty, price, gst_rate, total))

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(item_name))
                self.table.setItem(row, 1, QTableWidgetItem(str(qty)))
                self.table.setItem(row, 2, QTableWidgetItem(f"₹{price:.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{gst_rate}%"))
                self.table.setItem(row, 4, QTableWidgetItem(f"₹{total:.2f}"))

                self.update_total()
                logging.info(f"Item '{item_name}' added to cart. Qty: {qty}, Price: {price}, GST: {gst_rate}%, Total: {total}")
            except ValueError:
                logging.warning(f"Invalid GST rate entered: '{gst_rate_text}'.")
                QMessageBox.warning(self, "Invalid GST", "Please select a valid GST rate.")
        else:
            logging.warning("No item selected in the combobox.")
            QMessageBox.warning(self, "No Item Selected", "Please select an item to add to the cart.")

    def update_total(self):
        total = sum(item[4] for item in self.cart)
        self.total_label.setText(f"Total: ₹{total:.2f}")
        logging.info(f"Cart total updated: ₹{total:.2f}")

    def open_add_product_dialog(self):
        logging.info("Opening Add New Product dialog.")
        dialog = AddProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            logging.info("Add New Product dialog accepted. Reloading inventory.")
            self.inventory = fetch_inventory()
            self.update_inventory_combobox()
        else:
            logging.info("Add New Product dialog cancelled.")

    def generate_bill(self):
        logging.info("Generate Bill button clicked.")
        if not self.cart:
            QMessageBox.warning(self, "Cart Empty", "Please add some items first!")
            logging.warning("Generate Bill clicked with an empty cart.")
            return

        order_number = f"ORD-{int(time.time())}"
        filename = f"bill_{order_number}.pdf"

        # Get the user's Documents directory
        documents_dir = os.path.expanduser("~/Documents")
        orders_dir = os.path.join(documents_dir, "globizz_billing_orders")

        # Create the 'globizz_billing_orders' directory if it doesn't exist
        os.makedirs(orders_dir, exist_ok=True)
        filepath = os.path.join(orders_dir, filename)

        logging.info(f"Attempting to save bill to: {filepath}, Order No: {order_number}")
        self.generate_pdf(filepath, order_number)
        logging.info(f"PDF generation for Order No: {order_number} completed successfully and saved to: {filepath}")
        QMessageBox.information(self, "Success", f"Bill saved successfully to: {filepath}")

    def generate_pdf(self, filepath, order_number):
        logging.info(f"Starting generate_pdf for filepath: {filepath}, order_number: {order_number}")

        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph("Globizz Solutions", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Order No: {order_number}", styles['Normal']))
            elements.append(Paragraph(f"Date: {time.strftime('%d.%m.%Y')}", styles['Normal']))
            elements.append(Spacer(1, 12))

            # Table
            data = [["Sr.No", "Material Code", "U/M", "Qty", "Unit Price", "GST%", "Total"]]
            for idx, (item, qty, price, gst, total_item) in enumerate(self.cart, start=1):
                # Assuming 'material_code' is the second element in the item tuple from fetch_inventory
                material_code = self.inventory[self.item_combo.findText(item)][2] if self.item_combo.findText(item) != -1 else "N/A"
                data.append([str(idx), material_code, "Nos", str(qty), f"₹{price:.2f}", f"{gst}%", f"₹{total_item:.2f}"])

            table = Table(data, colWidths=[40, 150, 50, 40, 60, 40, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

            net_total = sum(item[4] for item in self.cart)
            elements.append(Paragraph(f"<b>Net Total: ₹{net_total:.2f}</b>", styles['Heading2']))

            elements.append(Spacer(1, 24))
            elements.append(Paragraph("For Globizz Solutions", styles['Normal']))
            elements.append(Spacer(1, 36))
            elements.append(Paragraph("Authorized Signatory", styles['Normal']))

            doc.build(elements)
            logging.info(f"PDF document for Order No: {order_number} built successfully at: {filepath}")

        except Exception as e:
            logging.error(f"Error during PDF generation for Order No: {order_number}: {e}", exc_info=True)

# --- Main ---
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BillingApp()
    window.show()
    exit_code = app.exec_()
    logging.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()