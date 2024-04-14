monthly_salary = 65  # Monthly salary in rupees
weekly_salary = monthly_salary / 4  # Weekly salary in rupees

total_activity_hours = 5  # Total activity hours for the week

# Calculate the amount earned for the week based on total activity hours
if total_activity_hours >= 40:
    week_earned = weekly_salary  # If 40 or more hours are worked, full weekly salary is earned
else:
    week_earned = (total_activity_hours / 40) * weekly_salary  # Calculate proportionate salary for hours worked

print("Weekly salary:", weekly_salary)
print("Amount earned for the week based on total activity hours:", week_earned)
