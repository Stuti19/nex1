import requests
import os
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
import tempfile

def extract_images_from_pdf_url(pdf_url, output_dir=None):
    """
    Extracts images from a PDF at a given URL using the Marker library.

    Args:
        pdf_url (str): The URL of the PDF.
        output_dir (str, optional): The directory to save the extracted images. 
                                     If None, a temporary directory is used.

    Returns:
        list: A list of filepaths to the extracted images, or None if an error occurs.
    """
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(response.content)
            pdf_path = temp_pdf.name

        if output_dir is None:
            output_dir = tempfile.mkdtemp()

        converter = PdfConverter(artifact_dict=create_model_dict())
        rendered = converter(pdf_path)
        _, _, images = text_from_rendered(rendered)

        image_paths = []
        for image_data in images:
            image_filename = os.path.join(output_dir, f"{image_data['id']}.png")
            with open(image_filename, "wb") as image_file:
                image_file.write(image_data["data"])
            image_paths.append(image_filename)

        os.unlink(pdf_path) # delete temporary PDF.
        return image_paths

    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    except Exception as e:
        print(f"Error extracting images: {e}")
        return None

#Example usage.
pdf_url = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/eacecae1-c000-4440-bac2-94036344d565.pdf"
image_output_dir = "extracted_images"  # Replace with the desired output directory

if not os.path.exists(image_output_dir):
    os.makedirs(image_output_dir)

image_paths = extract_images_from_pdf_url(pdf_url, image_output_dir)

if image_paths:
    print("Images extracted successfully:")
    for path in image_paths:
        print(path)
else:
    print("Image extraction failed.")