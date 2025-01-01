from ultralytics import YOLO
import os
import json
from PIL import Image

def food_detect(input_image_path):
    # Load the model
    model = YOLO('best.pt')  # Ensure the path to your best.pt is correct

    # Run inference on the image
    results = model(input_image_path,conf=0.8)

    # Extract the base name of the input image
    input_filename = os.path.basename(input_image_path)
    filename_without_ext, ext = os.path.splitext(input_filename)

    # Ensure the output directory exists
    output_dir = 'test_images/output/'
    os.makedirs(output_dir, exist_ok=True)

    # Save the annotated image
    output_image_path = os.path.join(output_dir, f'{filename_without_ext}_output{ext}')
    results[0].save(filename=output_image_path)

    # Load the saved image for display
    output_image = Image.open(output_image_path)

    # Extract food names, confidence scores, and count occurrences
    food_counts = {}
    for result in results:
        for box in result.boxes:
            food_name = model.names[int(box.cls)]  # Class name
            confidence = float(box.conf)           # Confidence score

            if food_name in food_counts:
                food_counts[food_name]['count'] += 1
                if confidence<0.8:
                    continue
                food_counts[food_name]['confidences'].append(confidence)
            else:
                food_counts[food_name] = {
                    'count': 1,
                    'confidences': [confidence]
                }

    # Prepare the final JSON structure
    detected_foods = [
        {
            "food_name": food_name,
            "food_count": info["count"],
            "confidence": max(info["confidences"])  # Return the highest confidence
        }
        for food_name, info in food_counts.items()
    ]

    json_output = json.dumps(detected_foods, indent=4)
    return json_output, output_image
