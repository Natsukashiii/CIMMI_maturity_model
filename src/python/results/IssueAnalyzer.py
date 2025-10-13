import pandas as pd
import plotly.graph_objects as go

# Load your CSV
df = pd.read_csv("../data/issue_responses.csv")

# Clean and convert relevant columns to boolean
for col in [
    "Closed",
    "Commented",
    "No English response",
    "Not interested",
    "Interested",
    "Spam",
    "Not applicable",
    "Don't agree",
    "Feedback",
    "Agree",
    "Recognize automations",
    "Model feedback",
    "Suggest task implementations",
]:
    df[col] = df[col].fillna(0).astype(bool)

# Basic counts
# Filter relevant entries: commented or closed
relevant = df[df["Commented"] | df["Closed"]]
total = len(relevant)
commented = relevant[relevant["Commented"]]

closed = relevant[relevant["Closed"] & ~relevant["Commented"]]
not_interested = commented[commented["Not interested"]]
interested = commented[commented["Interested"]]
not_in_english = commented[commented["No English response"]]

spam = not_interested[not_interested["Spam"]]
not_applicable = commented[commented["Not applicable"]]
dont_agree = not_interested[not_interested["Don't agree"]]

feedback = interested[interested["Feedback"]]
agree = interested[interested["Agree"]]

recognize = feedback[feedback["Recognize automations"]]
model = feedback[feedback["Model feedback"]]
suggest = feedback[feedback["Suggest task implementations"]]

labels = [
    "Total",
    "Closed",
    "Not interested",
    "Interested",
    "No English response",
    "Spam",
    "Not applicable",
    "Don't agree",
    "Feedback",
    "Agree",
]
label_indices = {label: i for i, label in enumerate(labels)}

# Define flows
source = []
target = []
value = []


def add_flow(from_label, to_label, count):
    source.append(label_indices[from_label])
    target.append(label_indices[to_label])
    value.append(count)


# Total ➝ Closed, Not interested, Interested
add_flow("Total", "Closed", len(closed))
add_flow("Total", "Not interested", len(not_interested))
add_flow("Total", "Interested", len(interested))
add_flow("Total", "No English response", len(not_in_english))
add_flow("Total", "Not applicable", len(not_applicable))

# Not interested ➝ Spam, Not applicable, Don't agree
add_flow("Not interested", "Spam", len(spam))
add_flow("Not interested", "Don't agree", len(dont_agree))

# Interested ➝ Feedback, Agree
add_flow("Interested", "Feedback", len(feedback))
add_flow("Interested", "Agree", len(agree))


# Modify your labels to include counts
labels_with_counts = [
    f"Total ({total})",
    f"Closed ({len(closed)})",
    f"Not interested ({len(not_interested)})",
    f"Interested ({len(interested)})",
    f"No English response ({len(not_in_english)})",
    f"Spam ({len(spam)})",
    f"Not applicable ({len(not_applicable)})",
    f"Don't agree ({len(dont_agree)})",
    f"Feedback ({len(feedback)})",
    f"Agree ({len(agree)})",
]

# Update the Sankey diagram creation
fig = go.Figure(
    data=[
        go.Sankey(
            node=dict(
                label=labels_with_counts,  # Use the new labels with counts
                pad=15,
                thickness=20,
                hovertemplate="%{label}<extra></extra>",  # Cleaner hover
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                hovertemplate="%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>",
            ),
        )
    ]
)
fig.update_layout(font=dict(size=20))
fig.show()


# Load your data
df = pd.read_csv("../data/issue_responses.csv")  # Replace with your actual file path

# Fill NA values for relevant columns
for col in [
    "Closed",
    "Commented",
    "Interested",
    "Not interested",
    "No English response",
    "Recognize automations",
    "Model feedback",
    "Use",
    "Not use",
    "Spam",
    "Not applicable",
    "Feedback",
    "Agree",
    "Don't agree",
]:
    df[col] = df[col].fillna(0)
not_closed_and_not_commented = df[(df["Closed"] == 0) & (df["Commented"] == 0)]

# Count metrics
totals = {
    "Total Issues": len(df),
    "Closed": df["Closed"].sum(),
    "Commented": df["Commented"].sum(),
    "Not closed and not commented": len(not_closed_and_not_commented),
    "Interested": df["Interested"].sum(),
    "Not Interested": df["Not interested"].sum(),
    "No English response": df["No English response"].sum(),
    "Would Use": df["Use"].sum(),
    "Would Not Use": df["Not use"].sum(),
    "Spam": df["Spam"].sum(),
    "Not applicable": df["Not applicable"].sum(),
    "Feedback Given": df["Feedback"].sum(),
    "Agree": df["Agree"].sum(),
    "Don't agree": df["Don't agree"].sum(),
    "Recognize automations": df["Recognize automations"].sum(),
    "Model feedback": df["Model feedback"].sum(),
}

# Convert to DataFrame for display
totals_df = pd.DataFrame(list(totals.items()), columns=["Metric", "Count"])

# Display the table
print(totals_df)
