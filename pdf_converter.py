import io
import fitz  # PyMuPDF
from PIL import Image

class PDFConverter:
    def pdf_to_images(self, pdf_binary, output_format='PNG', dpi=300):
        """
        Convert a PDF binary to a list of images without using poppler.
        
        :param pdf_binary: Bytes object containing the PDF data
        :param output_format: Output image format (default: 'PNG')
        :param dpi: DPI for rendering (default: 300)
        :return: List of PIL Image objects
        """
        # Open the PDF from binary data
        pdf_document = fitz.open(stream=pdf_binary, filetype="pdf")
        
        formatted_images = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Set the rendering matrix for desired DPI
            zoom = dpi / 72  # 72 is the default DPI
            matrix = fitz.Matrix(zoom, zoom)
            
            # Render page to an image
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to PIL Image and append to list
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to desired format
            if output_format != 'PNG':
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=output_format)
                img = Image.open(img_byte_arr)
            
            formatted_images.append(img)
        
        pdf_document.close()
        return formatted_images
