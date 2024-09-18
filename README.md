# Critical cGap Finder

## Project Overview

The **Critical cGap Finder** app is designed to analyze and identify the most critical GAPs (Good Agricultural Practices) based on an input Excel file named **"Master GAP Table with revised GAPs."** This file is provided by regional regulatory managers and contains requested GAPs categorized by country, crop, and product.

### Crop Information

For this project, we have excluded the following crops: 
- Rye
- Triticale
- Spelt
- Oat

Additionally, some crops have been grouped together, such as:
- Barley (Spring & Winter)
- Wheat (Durum, Spring, Winter)
- Cabbage
- Onion
- Rape

## Functionality

The app identifies the most critical GAPs by:
- Formulation (J-neck)
- Regulatory Zone (G-collar)
- Crop (O-collar)

### Criteria for Defining the Most Critical GAP

The following five criteria are used to determine the most critical GAP:
1. **Application Rate (g/ha)**: Higher rates are considered more critical.
2. **BBCH Stage**: The latest stage is deemed more critical.
3. **PHI (Pre-Harvest Interval)**: Shorter intervals are more critical.
4. **Interval Between Applications**: Smaller intervals are more critical.
5. **Number of Applications**: Higher values of Application Rate multiplied by the number of applications are more critical.

## Installation

To run the app, ensure you have the necessary dependencies installed. The main Python file is located in the **dashboard** folder and contains the following code snippet to run the app:

```python
if __name__ == '__main__':
    app.run_server(debug=True)