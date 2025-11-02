from io import BytesIO
from xhtml2pdf import pisa
from django.utils import timezone


def generate_ebook_pdf(book):
    """Generate a dynamic PDF for the eBook"""

    # HTML content for the PDF
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A5;
                margin: 2cm;
                @top-left {{
                    content: "{book.title}";
                    font-size: 10pt;
                }}
                @top-right {{
                    content: "Page " counter(page);
                    font-size: 10pt;
                }}
            }}

            body {{
                font-family: 'Georgia', serif;
                line-height: 1.6;
                color: #333;
            }}

            .cover-page {{
                page-break-after: always;
                text-align: center;
                padding-top: 8cm;
            }}

            .book-title {{
                font-family: 'Times New Roman', serif;
                font-size: 28pt;
                font-weight: bold;
                margin-bottom: 2cm;
                line-height: 1.3;
                color: #2c1810;
            }}

            .book-author {{
                font-family: 'Times New Roman', serif;
                font-size: 18pt;
                font-style: italic;
                color: #666;
                margin-bottom: 4cm;
            }}

            .publisher {{
                font-size: 12pt;
                color: #888;
                margin-top: 3cm;
            }}

            .content-page {{
                page-break-after: always;
                padding-top: 3cm;
            }}

            .chapter-title {{
                font-size: 20pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 2cm;
                color: #2c1810;
            }}

            .content {{
                font-size: 12pt;
                text-align: justify;
            }}

            .notice {{
                background-color: #f8f9fa;
                border-left: 4px solid #8B4513;
                padding: 20px;
                margin: 20px 0;
                font-style: italic;
            }}

            .copyright {{
                position: fixed;
                bottom: 2cm;
                left: 2cm;
                right: 2cm;
                text-align: center;
                font-size: 10pt;
                color: #666;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <!-- Cover Page -->
        <div class="cover-page">
            <div class="book-title">{book.title}</div>
            <div class="book-author">by {', '.join([author.name for author in book.authors.all()])}</div>
            <div class="publisher">BookNook Press</div>
        </div>

        <!-- Content Page 1 -->
        <div class="content-page">
            <div class="chapter-title">About This Book</div>
            <div class="content">
                <p><strong>Genre:</strong> {book.genre.name}</p>
                <p><strong>Publication Year:</strong> {book.publication_year}</p>
                <p><strong>ISBN:</strong> {book.isbn}</p>

                <div class="notice">
                    <p>This is an auto-generated preview of the eBook. The full content is available in the purchased version.</p>
                    <p>The complete eBook includes the entire text with proper formatting, chapters, and additional features.</p>
                </div>

                <h3>Summary</h3>
                <p>{book.summary}</p>
            </div>
        </div>

        <!-- Content Page 2 -->
        <div class="content-page">
            <div class="chapter-title">Sample Content</div>
            <div class="content">
                <div class="notice">
                    <p>This PDF represents a preview of the eBook format. In a real implementation, this would contain:</p>
                    <ul>
                        <li>Complete book text with proper chapter divisions</li>
                        <li>Interactive table of contents</li>
                        <li>Bookmarks and annotations support</li>
                        <li>Adjustable font sizes and reading themes</li>
                        <li>Search functionality within the text</li>
                    </ul>
                    <p>The actual eBook would be delivered in EPUB or MOBI format for optimal reading experience across devices.</p>
                </div>

                <h3>Why Choose eBooks?</h3>
                <p>eBooks from BookNook offer:</p>
                <ul>
                    <li>Instant delivery after purchase</li>
                    <li>Read on any device - phone, tablet, or computer</li>
                    <li>Adjustable text size for comfortable reading</li>
                    <li>Environmentally friendly - no paper waste</li>
                    <li>Always with you in your digital library</li>
                </ul>
            </div>
        </div>

        <!-- Copyright Page -->
        <div class="content-page">
            <div class="content">
                <div class="copyright">
                    © {timezone.now().year} BookNook. All rights reserved.<br>
                    This eBook is licensed to the purchaser for personal use only.<br>
                    Unauthorized distribution is prohibited.
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

    if pisa_status.err:
        return None

    pdf_file.seek(0)
    return pdf_file.getvalue()


def generate_preview_pdf(book):
    """Generate a preview PDF with limited content"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A5;
                margin: 2cm;
            }}

            body {{
                font-family: 'Georgia', serif;
                line-height: 1.6;
                color: #333;
            }}

            .cover-page {{
                page-break-after: always;
                text-align: center;
                padding-top: 8cm;
            }}

            .book-title {{
                font-family: 'Times New Roman', serif;
                font-size: 28pt;
                font-weight: bold;
                margin-bottom: 2cm;
                line-height: 1.3;
                color: #2c1810;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}

            .book-author {{
                font-family: 'Times New Roman', serif;
                font-size: 18pt;
                font-style: italic;
                color: #666;
                margin-bottom: 4cm;
                letter-spacing: 1px;
            }}

            .preview-notice {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 30px;
                margin: 50px 0;
                text-align: center;
                border-radius: 5px;
            }}

            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 48pt;
                color: rgba(0,0,0,0.1);
                z-index: -1;
            }}
        </style>
    </head>
    <body>
        <div class="watermark">PREVIEW</div>

        <!-- Cover Page -->
        <div class="cover-page">
            <div class="book-title">{book.title}</div>
            <div class="book-author">by {', '.join([author.name for author in book.authors.all()])}</div>
            <div style="color: #888; margin-top: 3cm;">BookNook Preview Edition</div>
        </div>

        <!-- Preview Content -->
        <div style="page-break-after: always; padding-top: 3cm;">
            <h1 style="text-align: center; color: #2c1810;">Preview</h1>

            <div class="preview-notice">
                <h2>✨ Book Preview</h2>
                <p>This is a preview of <strong>"{book.title}"</strong> by {', '.join([author.name for author in book.authors.all()])}.</p>
                <p>The complete eBook includes the full content with proper formatting and additional features.</p>
            </div>

            <h3>About This Book</h3>
            <p><strong>Genre:</strong> {book.genre.name}</p>
            <p><strong>Published:</strong> {book.publication_year}</p>

            <h3>Summary</h3>
            <p>{book.summary}</p>

            <div style="text-align: center; margin-top: 3cm; padding: 20px; border-top: 1px solid #ddd;">
                <p><em>This preview shows the eBook format and quality.</em></p>
                <p><strong>Purchase the full eBook to enjoy the complete reading experience!</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

    if pisa_status.err:
        return None

    pdf_file.seek(0)
    return pdf_file.getvalue()
