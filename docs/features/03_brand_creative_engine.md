# Features: Brand Creative Engine

## 1. Overview
The Brand Creative Engine transforms the standard ERPNext `Brand` DocType from a simple name-only record into a comprehensive interactive design studio. It allows marketing teams to define, visualize, and synchronize their visual identity across all BizMarketing collateral.

## 2. Core Features

### 2.1 Visual Color Selection
Integrated **Color Pickers** allow users to select and store exact hex codes for:
- **Primary Color**: The dominant brand color (used for headings and primary buttons).
- **Secondary Color**: Supporting color for accents and variety.
- **Accent Color**: High-contrast color for Call-to-Action elements.

### 2.2 Advanced Typography Engine
A curated selector for professional Google-font paired typography:
- **Font Selection**: Options include *Inter, Roboto, Outfit, Open Sans, Poppins, Montserrat, Lato, Oswald, Raleway, and Playfair Display*.
- **Heading Weight**: Configurable font weights from 400 (Normal) to 900 (Black).
- **Base Font Size**: Global base sizing in pixels (defaulting to 16px).

### 2.3 Interactive Live Preview
The most advanced feature is the **Live Brand Preview** wrapper. This is a custom HTML field injected via client script that renders a real-time mock-up of the brand:
- **Dynamic CSS Injection**: Changes to color and font fields are immediately applied to the preview window without saving.
- **Visual Components**:
  - **Typography Hierarchy**: H1 through H4 examples with proper sizing.
  - **Paragraph Text**: Body text rendering with the selected font.
  - **Interactive Elements**: Buttons and links showing primary and accent colors.
  - **Color Swatches**: Visual boxes displaying the hex codes and colors.

## 3. Implementation Details

### Fixtures & Overrides
The engine is implemented using Frappe **Fixtures**:
- **Custom Fields**: New fields for colors, typography, and preview.
- **Client Script**: The "Brand" Client Script contains the logic for:
  - Monitoring field changes via `frm.on_change`.
  - Injecting a `<style>` block into the form's shadow DOM or wrapper.
  - Asynchronously rendering the HTML preview template.

### UI Structure (Tabs)
The Brand form is organized into logical tabs:
1. **Brand Identity**: Logo and Color palette.
2. **Strategic Vision**: Mission, Vision, and Tone of Voice.
3. **Assets & Links**: Brand guidelines and social links.
4. **Live Preview**: Full-screen visual feedback loop.

## 4. Business Logic Integration
The `Brand` record is linked to:
- **Marketing Strategy**: Ensures strategic goals align with visual tone.
- **Marketing Campaign**: Drives consistent asset creation.
- **Social Media Post**: Future-proofed for automated graphic generation based on brand tokens.
