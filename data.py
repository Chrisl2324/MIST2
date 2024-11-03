import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Define the number of samples you want
num_samples = 1000

# Generate random engine names
engine_names = [f"engine_{i}" for i in range(num_samples)]

# Generate random submission dates in the past 10 years
start_date = datetime.now() - timedelta(days=3650)  # 10 years ago
submission_dates = [start_date + timedelta(days=np.random.randint(0, 3650)) for _ in range(num_samples)]

# Generate random values for other columns
power_output = np.random.randint(1, 11, size=num_samples)  # Random integers from 1 to 10
pressure = np.random.randint(1, 11, size=num_samples)
velocity = np.random.randint(1, 11, size=num_samples)
acceleration = np.random.randint(1, 11, size=num_samples)
weight = np.random.randint(1, 11, size=num_samples)

# Create a more complicated failure condition
failure_conditions = (
    (power_output < 4) |                        # Power output is less than 4
    (weight > 7) |                              # Weight is greater than 7
    (pressure < 3) |                            # Pressure is below 3
    (velocity > 8) |                            # Velocity is greater than 8
    (acceleration >= 6) |                       # Acceleration is greater than or equal to 6
    ((power_output + pressure) < 6)            # Combined condition: power output + pressure < 6
)

# Create the failure column based on the conditions
failure = failure_conditions

# Create the DataFrame
data = {
    "engineName": engine_names,
    "submissionDate": submission_dates,
    "powerOutput": power_output,
    "pressure": pressure,
    "velocity": velocity,
    "acceleration": acceleration,
    "weight": weight,
    "failure": failure,
}

df = pd.DataFrame(data)

# Display the DataFrame
print(df)

# Optionally, save to CSV
df.to_csv('engine_data_with_complex_failure.csv', index=False)
