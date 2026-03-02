from reportlab.pdfgen import canvas

c = canvas.Canvas("test.pdf")
c.drawString(100, 750, "My name is John Doe and my phone number is 555-1234")
c.save()
