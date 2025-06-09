import serial
import time
import os
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array, load_img
from picamera2 import Picamera2, Preview
import I2C_LCD_driver  # Ensure LCD driver is installed

# Initialize LCD
lcd = I2C_LCD_driver.lcd()

# Set up serial communication with Arduino
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for connection to establish

# Load the trained model and label encoder
model = load_model('fruit_detector_model.h5')
label_encoder = np.load('label_encoder.npy', allow_pickle=True)

# Constants
CAPTURED_PHOTO = "captured_photo.jpg"
last_image = None

def update_lcd(message, line=1, clear=True):
    """Update the LCD display with a given message."""
    if clear:
        lcd.lcd_clear()
    lcd.lcd_display_string(message, line)

def scroll_text(text, line=1, delay=0.3):
    """Scroll long text across the LCD display."""
    lcd.lcd_clear()
    text = " " * 16 + text + " " * 16  # Add spaces for smooth scrolling
    for i in range(len(text) - 15):
        lcd.lcd_display_string(text[i:i+16], line)
        time.sleep(delay)

def capture_image(filename=CAPTURED_PHOTO):
    """Captures an image using Picamera2."""
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
    picam2.configure(preview_config)
    
    picam2.start_preview(Preview.QTGL)
    picam2.start()
    
    update_lcd("Photo Capturing...", 1)
    
    print("Press Enter to capture an image...")
    input()  # Wait for user input to capture
    
    picam2.capture_file(filename)
    print(f"Image captured: {filename}")
    
    update_lcd("Captured!", 1)
    time.sleep(1)  # Briefly show "Captured!" message
    
    scroll_text("Photo Sent to Model", 1)  # Scrolling text
    
    picam2.stop()

def load_and_prepare_image(image_path):
    """Load and preprocess the image for model prediction."""
    try:
        image = load_img(image_path, target_size=(100, 100))  # Resize image
        image = img_to_array(image) / 255.0  # Normalize pixel values
        return np.expand_dims(image, axis=0)  # Add batch dimension
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def predict_fruit(image_path):
    """Predict the fruit type from the given image."""
    image = load_and_prepare_image(image_path)
    if image is None:
        update_lcd("Error: Unable", 1)
        update_lcd("To Load Image", 2)
        return "Error loading image"
    
    time.sleep(1)  # **Wait for 1 second before showing result**
    
    prediction = model.predict(image)
    predicted_label_index = np.argmax(prediction)
    confidence = prediction[0][predicted_label_index]

    if confidence < 0.5:
        update_lcd("Taking Turn", 1)
        return "Unrecognized object detected"
    else:
        predicted_label = label_encoder[predicted_label_index]
        update_lcd(predicted_label, 1)
        update_lcd("Picking Fruit", 2)
        return f"{predicted_label} {confidence * 100:.2f}%"

def take_photo():
    """Handles capturing and managing the latest photo, then performs fruit detection."""
    global last_image
    capture_image(CAPTURED_PHOTO)
    
    if last_image and last_image != CAPTURED_PHOTO:
        os.remove(last_image)
        print(f"Deleted old image: {last_image}")
    
    last_image = CAPTURED_PHOTO
    arduino.write(b'r')  # Notify Arduino to resume
    
    # Perform fruit detection
    result = predict_fruit(CAPTURED_PHOTO)
    print(f"Fruit Detection Result: {result}")

def main():
    try:
        print("Car Control Interface")
        print("Commands:")
        print("  w - Move forward")
        print("  a - Turn left")
        print("  d - Turn right")
        print("  s - Move backward")
        print("  x - Stop motors")
        print("  q - Standard servo 30 degrees left")
        print("  e - Standard servo 30 degrees right")
        print("  u - Stop continuous servo")
        print("  Q - Continuous servo rotate left")
        print("  E - Continuous servo rotate right")
        print("  v - Capture Image and Detect Fruit")
        print("  z - Quit")

        while True:
            command = input("Enter command: ").strip()
            
            if command in ['w', 'a', 'd', 's', 'x', 'q', 'e', 'u', 'Q', 'E']:
                arduino.write(command.encode())  # Send command to Arduino
                action_messages = {
                    'w': "Moving Forward",
                    'a': "Turning Left",
                    'd': "Turning Right",
                    's': "Moving Backward",
                    'x': "Stopped",
                    'q': "Servo Left 30°",
                    'e': "Servo Right 30°",
                    'u': "Stopping Servo",
                    'Q': "Servo Rot. Left",
                    'E': "Servo Rot. Right"
                }
                update_lcd(action_messages.get(command, "Executing"), 1)
                print(f"Sent command: {command}")
            elif command == 'v':
                take_photo()
            elif command == 'z':
                update_lcd("Exiting...", 1)
                print("Exiting...")
                break  # Exit the loop and terminate the program
            else:
                print("Invalid command. Please use valid commands: 'w', 'a', 'd', 's', 'x', 'q', 'e', 'u', 'Q', 'E', 'v', or 'z'.")

    except serial.SerialException as e:
        update_lcd("Serial Error", 1)
        print(f"Error connecting to Arduino: {e}")
    except KeyboardInterrupt:
        update_lcd("Exiting...", 1)
        print("\nExiting due to keyboard interrupt.")
    finally:
        if 'arduino' in locals() and arduino.is_open:
            arduino.close()
            update_lcd("Serial Closed", 1)
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
