import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FROM_EMAIL = "pavithavaranam2003@gmail.com"
PASSWORD = "pavi@123"  
# Replace with your email password
DB_CONFIG = {
    'user': 'root',
    'password': '12345',
    'host': 'localhost',
    'database': 'ticket_db'
}
GST_RATE = 0.18

def fetch_ticket_details(ticket_code):
    """Fetch ticket details from the database."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT price FROM valid_tickets WHERE ticket_code = %s", (ticket_code,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            return result[0]
        return None
    except Error as e:
        logging.error(f"Error fetching ticket details: {e}")
        return None

def send_email(to_email, subject, body):
    """Send an email using SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(FROM_EMAIL, PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email} with subject '{subject}'.")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")

def calculate_gst(price):
    """Calculate GST for the given price."""
    gst_amount = price * GST_RATE
    total_price = price + gst_amount
    return total_price, gst_amount

def book_ticket(name, ticket_code, email):
    """Book a ticket and store the booking details in the database."""
    price = fetch_ticket_details(ticket_code)
    
    if price is None:
        logging.info(f"Ticket code {ticket_code} is invalid for booking.")
        send_email(email, "Ticket Booking Failed", "The ticket code you provided is invalid.")
        return False
    
    total_price, gst_amount = calculate_gst(price)
    booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO bookings (name, ticket_code, email, total_price) VALUES (%s, %s, %s, %s)",
                       (name, ticket_code, email, total_price))
        connection.commit()
        cursor.close()
        connection.close()
        logging.info(f"Ticket booked successfully for {name} with ticket code {ticket_code}. Total price: {total_price} (including GST: {gst_amount})")
        send_email(email, "Ticket Booking Confirmation",
                   f"Your ticket has been booked successfully.\n\nName: {name}\nTicket Code: {ticket_code}\nBooking Time: {booking_time}\nBase Price: {price}\nGST (18%): {gst_amount}\nTotal Price: {total_price}\n\nEnjoy the show!")
        return True
    except Error as e:
        logging.error(f"Error booking ticket: {e}")
        send_email(email, "Ticket Booking Failed", "There was an error booking your ticket. Please try again.")
        return False

def main():
    """Main function to run the ticket booking process."""
    # Example usage
    bookings = [
        ("John Doe", "PAVI123", "pavithauma@gmail.com"),
        ("Jane Doe", "INVALID_CODE", "pavithauma@gmail.com")
    ]

    for name, ticket_code, email in bookings:
        logging.info(f"Booking ticket for {name} with ticket code {ticket_code}.")
        book_ticket(name, ticket_code, email)

if __name__ == "__main__":
    main()