# How to use FPL_2025.csv for Charity Care screening

- Use patient's household_size and annual_income.
- Select region by state: 
  - Alaska -> alaska
  - Hawaii -> hawaii
  - Otherwise -> contiguous
- Compare income to FPL multiples defined in the hospital's FAP.
- Example: If FAP says "<=200% FPL", compute:
  threshold = FPL_2025(region, household_size) * 2.0
