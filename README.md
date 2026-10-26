# BFB321 Group 4 Semester Project - MedSync Supply Chain Web Application

## Project Description
Digitizing Medicine Supply Chains to Reduce Stockouts in South African Public Healthcare. This application helps medical facilities calculate and track inventory metrics including Economic Order Quantity (EOQ), Safety Stock (SS), and Reorder Points (ROP) to streamline medical supplies management.

## Group Members & Student Numbers
| Student Name | Student Number |
| :--- | :--- |
| Meagan Staples | u24645177 |
| Despina Papageorgiou | u24627527 |
| Callum Kenyon-Slade | u24721787 |

## Setup & Installation Instructions

### Prerequisites
- Python 3.10+
- Git

### Installation Steps
1. Clone the repository:
   ```
   git clone https://github.com/u24645177/BFB321_Group4_Project.git
   cd BFB321_Group4_Project
   ```

2. Set up a virtual environment:
   - Windows:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install dependencies:
   ```
   pip install flask pytest
   ```

4. Run the application:
   ```
   python app.py
   ```
   Then open http://localhost:5001 in your web browser.

5. Run the test suite:
   ```
   python -m pytest tests/
   ```