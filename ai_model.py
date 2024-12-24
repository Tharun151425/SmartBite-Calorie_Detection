from ultralytics import YOLO
import os
import json
from PIL import Image

def food_detect(input_image_path):
    # Load the model
    model = YOLO('best.pt')  # Ensure the path to your best.pt is correct

    # Run inference on the image
    results = model(input_image_path)  # Specify the image path

    # Extract the base name of the input image (e.g., 'burger1.jpg')
    input_filename = os.path.basename(input_image_path)

    # Split the filename and extension
    filename_without_ext, ext = os.path.splitext(input_filename)

    # Ensure the output directory exists
    output_dir = 'test_images//output//'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Construct the output image path
    output_image_path = os.path.join(output_dir, f'{filename_without_ext}_output{ext}')

    # Save the image with detections
    results[0].save(filename=output_image_path)  # Save image

    # Load the saved image for display in Streamlit
    output_image = Image.open(output_image_path)

    # Extract food names and confidence scores, and convert to JSON format
    detected_foods = []
    for result in results:
        for box in result.boxes:
            food_info = {
                "food_name": model.names[int(box.cls)],  # Class name
                "confidence": float(box.conf)            # Confidence score
            }

            if len(detected_foods) == 0:
                detected_foods.append(food_info)

            temp1 = [i.get("food_name") for i in detected_foods]
            if food_info["food_name"] not in temp1:
                detected_foods += [food_info]
            
    print(detected_foods)
    # Convert the detected foods to JSON format
    json_output = json.dumps(detected_foods, indent=4)

    # Return both the JSON output and the image
    return json_output, output_image
