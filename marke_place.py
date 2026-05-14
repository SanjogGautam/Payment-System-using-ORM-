import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, ForeignKey, Numeric, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    payments: Mapped[list["Payment"]] = relationship(back_populates="customer")


class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(100))
    secret_key: Mapped[str] = mapped_column(String(255))
    products: Mapped[list["Product"]] = relationship(back_populates="vendor")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    vendor: Mapped["Vendor"] = relationship(back_populates="products")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="INITIATED")
    transaction_uuid: Mapped[str] = mapped_column(String(100), unique=True)
    gateway_ref_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    customer: Mapped["User"] = relationship(back_populates="payments")


# --- Setup ---
engine = create_engine("sqlite:///marketplace.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def seed_data():
    if session.query(Vendor).first():
        return  # already seeded

    v1 = Vendor(name="Sanjog's Store", location="Thamel, KTM", secret_key="secret_sanjog")
    v2 = Vendor(name="Sarin Traders", location="New Road, KTM", secret_key="secret_sarin")
    session.add_all([v1, v2])
    session.flush()

    session.add_all([
        Product(name="Handwoven Dhaka Topi", price=Decimal("850.00"), vendor_id=v1.id),
        Product(name="Yarsagumba Capsules",  price=Decimal("3200.00"), vendor_id=v1.id),
        Product(name="Himalayan Singing Bowl",price=Decimal("1500.00"), vendor_id=v2.id),
        Product(name="Organic Timur Pepper", price=Decimal("420.00"),  vendor_id=v2.id),
        Product(name="Pashmina Shawl",       price=Decimal("2800.00"), vendor_id=v1.id),
    ])

    customer = User(name="Swagat Kumar Khanal", email="swagat@gmail.com")
    session.add(customer)
    session.commit()
    print("✓ Sample data seeded.\n")


# --- Helpers ---
def divider():
    print("-" * 45)

def list_products():
    products = session.query(Product).all()
    print("\n  ID  Product                     Vendor           Price")
    divider()
    for p in products:
        print(f"  {p.id:<4} {p.name:<28} {p.vendor.name:<16} Rs {p.price}")
    print()

def list_vendors():
    vendors = session.query(Vendor).all()
    print("\n  ID  Vendor           Location")
    divider()
    for v in vendors:
        print(f"  {v.id:<4} {v.name:<16} {v.location}")
    print()

def show_payment_history(customer):
    payments = session.query(Payment).filter_by(customer_id=customer.id).all()
    if not payments:
        print("  No payments yet.\n")
        return
    print(f"\n  {'ID':<4} {'Product':<28} {'Amount':<12} {'Status':<10} {'Date'}")
    divider()
    for p in payments:
        product = session.get(Product, p.product_id)
        print(f"  {p.id:<4} {product.name:<28} Rs {str(p.amount):<10} {p.status:<10} {p.created_at.strftime('%Y-%m-%d %H:%M')}")
    print()


# --- Actions ---
def purchase_flow(customer):
    list_products()
    try:
        pid = int(input("  Enter Product ID to buy (0 to cancel): "))
    except ValueError:
        print("  Invalid input.\n"); return
    if pid == 0:
        return

    product = session.get(Product, pid)
    if not product:
        print("  Product not found.\n"); return

    print(f"\n  Product : {product.name}")
    print(f"  Vendor  : {product.vendor.name}")
    print(f"  Amount  : Rs {product.price}")
    print(f"\n  Gateways: 1) eSewa  2) Fonepay  3) Khalti")
    choice = input("  Choose gateway (1/2/3): ").strip()
    gateways = {"1": "eSewa", "2": "Fonepay", "3": "Khalti"}
    gateway = gateways.get(choice, "eSewa")

    confirm = input(f"\n  Pay Rs {product.price} via {gateway}? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.\n"); return

    txn_uuid = str(uuid.uuid4())
    payment = Payment(
        customer_id=customer.id,
        product_id=product.id,
        amount=product.price,
        status="INITIATED",
        transaction_uuid=txn_uuid,
        gateway_ref_id=None,
    )
    session.add(payment)
    session.commit()

    print(f"\n  ⏳ Processing via {gateway}...")
    # Simulate gateway response (always SUCCESS here; plug real API call here)
    gateway_ref = f"{gateway.upper()}-{uuid.uuid4().hex[:8].upper()}"
    payment.status = "SUCCESS"
    payment.gateway_ref_id = gateway_ref
    session.commit()

    print(f"  ✅ Payment SUCCESS")
    print(f"     Txn UUID   : {txn_uuid}")
    print(f"     Gateway Ref: {gateway_ref}\n")


def vendor_menu(vendor):
    while True:
        print(f"\n=== Vendor Portal — {vendor.name} ===")
        print("  1) View my products")
        print("  2) Add new product")
        print("  3) View my sales")
        print("  0) Back")
        choice = input("  Choice: ").strip()

        if choice == "1":
            products = session.query(Product).filter_by(vendor_id=vendor.id).all()
            print(f"\n  {'ID':<4} {'Product':<28} {'Price'}")
            divider()
            for p in products:
                print(f"  {p.id:<4} {p.name:<28} Rs {p.price}")
            print()

        elif choice == "2":
            name = input("  Product name: ").strip()
            try:
                price = Decimal(input("  Price (NPR): ").strip())
            except Exception:
                print("  Invalid price.\n"); continue
            p = Product(name=name, price=price, vendor_id=vendor.id)
            session.add(p)
            session.commit()
            print(f"  ✓ '{name}' added at Rs {price}\n")

        elif choice == "3":
            prod_ids = [p.id for p in session.query(Product).filter_by(vendor_id=vendor.id).all()]
            payments = session.query(Payment).filter(
                Payment.product_id.in_(prod_ids),
                Payment.status == "SUCCESS"
            ).all()
            total = sum(p.amount for p in payments)
            print(f"\n  Total sales: {len(payments)}  |  Revenue: Rs {total}\n")

        elif choice == "0":
            break


# --- Main ---
def main():
    seed_data()
    customer = session.query(User).filter_by(email="swagat@gmail.com").first()

    while True:
        print("=== BazarNP Marketplace ===")
        print("  1) Browse & buy products")
        print("  2) My order history")
        print("  3) Vendor portal")
        print("  0) Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            purchase_flow(customer)
        elif choice == "2":
            show_payment_history(customer)
        elif choice == "3":
            list_vendors()
            try:
                vid = int(input("  Enter Vendor ID: "))
            except ValueError:
                continue
            vendor = session.get(Vendor, vid)
            if vendor:
                vendor_menu(vendor)
            else:
                print("  Vendor not found.\n")
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()