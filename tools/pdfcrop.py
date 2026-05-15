import fitz

doc = fitz.open('/Users/flashlight/Documents/自学/海大/计算理论/Introduction-To-The-Theory-Of-Computation-Michael-Sipser.pdf')
rect = fitz.Rect(385, 385, 2098, 3150)
for page in doc:
    rect = page.rect
    new_rect = fitz.Rect(
        385 * (rect.x1 - rect.x0) / 2480,
        385 * (rect.y1 - rect.y0) / 3507,
        2098 * (rect.x1 - rect.x0) / 2480,
        3150 * (rect.y1 - rect.y0) / 3507,
                         )
    page.set_cropbox(new_rect)
doc.save('/Users/flashlight/Documents/自学/海大/计算理论/Introduction-To-The-Theory-Of-Computation-Michael-Sipser_croped.pdf')
doc.close()
