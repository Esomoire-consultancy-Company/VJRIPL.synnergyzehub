import time
import random

class ProductionDashboard:
    def __init__(self):
        self.production_data = []
        self.delivery_status = "Pending"
        self.notifications = []

    def monitor_production(self):
        # Simulate real-time production monitoring
        while True:
            data_point = random.randint(1, 100)
            self.production_data.append(data_point)
            print(f"Production Data Point: {data_point}")
            time.sleep(5)  # Wait for 5 seconds before the next data point

    def update_delivery_status(self, status):
        self.delivery_status = status
        print(f"Delivery Status Updated: {self.delivery_status}")

    def send_notification(self, message):
        self.notifications.append(message)
        print(f"Notification Sent: {message}")

if __name__ == '__main__':
    dashboard = ProductionDashboard()
    
    # Simulate the updating of delivery status and sending notifications
    dashboard.update_delivery_status("In Transit")
    dashboard.send_notification("Customer Notification: Your order is on the way!")
    
    # Start monitoring production in real-time
    dashboard.monitor_production()