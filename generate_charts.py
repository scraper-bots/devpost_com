#!/usr/bin/env python3
"""
Generate meaningful charts from Devpost hackathon data
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Read the data
print("Reading data...")
df = pd.read_csv('devpost_hackathons.csv')

print(f"Loaded {len(df)} hackathons")
print(f"Columns: {df.columns.tolist()}")

# Create charts directory if it doesn't exist
import os
os.makedirs('charts', exist_ok=True)

# Chart 1: Hackathon Status Distribution
print("\n1. Generating hackathon status distribution chart...")
fig, ax = plt.subplots(figsize=(10, 6))
status_counts = df['open_state'].value_counts()
colors = ['#e74c3c', '#2ecc71', '#3498db']
bars = ax.bar(range(len(status_counts)), status_counts.values, color=colors[:len(status_counts)])
ax.set_xticks(range(len(status_counts)))
ax.set_xticklabels(status_counts.index, fontsize=12)
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Hackathon Status Distribution', fontsize=16, fontweight='bold', pad=20)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, status_counts.values)):
    percentage = (value / len(df)) * 100
    ax.text(i, value + 100, f'{value:,}\n({percentage:.1f}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/01_status_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 2: Top 15 Organizations by Number of Hackathons
print("2. Generating top organizations chart...")
fig, ax = plt.subplots(figsize=(12, 8))
org_counts = df['organization_name'].value_counts().head(15)
bars = ax.barh(range(len(org_counts)), org_counts.values, color='#3498db')
ax.set_yticks(range(len(org_counts)))
ax.set_yticklabels(org_counts.index)
ax.set_xlabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Top 15 Organizations by Number of Hackathons', fontsize=16, fontweight='bold', pad=20)
ax.invert_yaxis()

# Add value labels
for i, (bar, value) in enumerate(zip(bars, org_counts.values)):
    ax.text(value + 0.5, i, str(value), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/02_top_organizations.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 3: Most Popular Themes
print("3. Generating popular themes chart...")
all_themes = []
for themes_str in df['themes'].dropna():
    if isinstance(themes_str, str):
        themes = [t.strip() for t in themes_str.split(',')]
        all_themes.extend(themes)

theme_counts = Counter(all_themes).most_common(15)
themes, counts = zip(*theme_counts)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(range(len(themes)), counts, color='#e74c3c')
ax.set_yticks(range(len(themes)))
ax.set_yticklabels(themes)
ax.set_xlabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Top 15 Most Popular Hackathon Themes', fontsize=16, fontweight='bold', pad=20)
ax.invert_yaxis()

# Add value labels
for i, (bar, value) in enumerate(zip(bars, counts)):
    ax.text(value + 10, i, str(value), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/03_popular_themes.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 4: Prize Distribution Analysis
print("4. Generating prize distribution chart...")
# Extract numeric prize amounts
def extract_prize_amount(prize_str):
    if pd.isna(prize_str) or prize_str == '':
        return 0
    # Remove dollar sign, commas, and extract numbers
    match = re.search(r'[\d,]+', str(prize_str))
    if match:
        return int(match.group().replace(',', ''))
    return 0

df['prize_numeric'] = df['prize_amount'].apply(extract_prize_amount)

# Filter out zero prizes and create bins
prizes_with_value = df[df['prize_numeric'] > 0]['prize_numeric']

fig, ax = plt.subplots(figsize=(12, 7))
bins = [0, 5000, 10000, 25000, 50000, 100000, 250000, 500000, max(prizes_with_value)]
labels = ['<$5K', '$5K-$10K', '$10K-$25K', '$25K-$50K', '$50K-$100K', '$100K-$250K', '$250K-$500K', '>$500K']
prize_bins = pd.cut(prizes_with_value, bins=bins, labels=labels[:len(bins)-1])
prize_counts = prize_bins.value_counts().sort_index()

bars = ax.bar(range(len(prize_counts)), prize_counts.values, color='#f39c12')
ax.set_xticks(range(len(prize_counts)))
ax.set_xticklabels(prize_counts.index, rotation=45, ha='right')
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Prize Amount Distribution (Hackathons with Prizes)', fontsize=16, fontweight='bold', pad=20)

# Add value labels
for i, (bar, value) in enumerate(zip(bars, prize_counts.values)):
    ax.text(i, value + 5, str(value), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/04_prize_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 5: Registration Distribution
print("5. Generating registration distribution chart...")
# Filter out very high outliers for better visualization
reg_data = df[df['registrations_count'] > 0]['registrations_count']
q99 = reg_data.quantile(0.99)
reg_filtered = reg_data[reg_data <= q99]

fig, ax = plt.subplots(figsize=(12, 7))
max_reg = max(reg_filtered)
# Create bins dynamically based on max value
bin_edges = [0, 100, 250, 500, 1000, 2500, 5000, 10000]
# Only include bins that are less than max value
bins = [b for b in bin_edges if b < max_reg] + [max_reg]
# Create labels dynamically
labels = []
for i in range(len(bins)-1):
    if i == 0:
        labels.append(f'<{bins[1]}')
    elif i == len(bins)-2:
        labels.append(f'>{bins[-2]}')
    else:
        labels.append(f'{bins[i]}-{bins[i+1]}')

reg_bins = pd.cut(reg_filtered, bins=bins, labels=labels)
reg_counts = reg_bins.value_counts().sort_index()

bars = ax.bar(range(len(reg_counts)), reg_counts.values, color='#9b59b6')
ax.set_xticks(range(len(reg_counts)))
ax.set_xticklabels(reg_counts.index, rotation=45, ha='right')
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Participant Registration Distribution', fontsize=16, fontweight='bold', pad=20)

# Add value labels
for i, (bar, value) in enumerate(zip(bars, reg_counts.values)):
    ax.text(i, value + 10, str(value), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/05_registration_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 6: Location Distribution (Top 20)
print("6. Generating location distribution chart...")
location_counts = df['location'].value_counts().head(20)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(range(len(location_counts)), location_counts.values, color='#1abc9c')
ax.set_yticks(range(len(location_counts)))
ax.set_yticklabels(location_counts.index)
ax.set_xlabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Top 20 Hackathon Locations', fontsize=16, fontweight='bold', pad=20)
ax.invert_yaxis()

# Add value labels
for i, (bar, value) in enumerate(zip(bars, location_counts.values)):
    ax.text(value + 10, i, str(value), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/06_location_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 7: Featured vs Non-Featured Hackathons
print("7. Generating featured hackathons chart...")
fig, ax = plt.subplots(figsize=(10, 6))
featured_counts = df['featured'].value_counts()
colors = ['#95a5a6', '#3498db']
labels = ['Non-Featured' if not x else 'Featured' for x in featured_counts.index]
bars = ax.bar(range(len(featured_counts)), featured_counts.values, color=colors[:len(featured_counts)])
ax.set_xticks(range(len(featured_counts)))
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Featured vs Non-Featured Hackathons', fontsize=16, fontweight='bold', pad=20)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, featured_counts.values)):
    percentage = (value / len(df)) * 100
    ax.text(i, value + 100, f'{value:,}\n({percentage:.1f}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/07_featured_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 8: Cash vs Other Prizes
print("8. Generating prize types comparison chart...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Cash prizes distribution
cash_data = df[df['cash_prizes_count'] > 0]['cash_prizes_count']
cash_bins = [0, 1, 3, 5, 10, max(cash_data) + 1]
cash_labels = ['1', '2-3', '4-5', '6-10', '>10']
cash_binned = pd.cut(cash_data, bins=cash_bins, labels=cash_labels, include_lowest=True)
cash_counts = cash_binned.value_counts().sort_index()

bars1 = ax1.bar(range(len(cash_counts)), cash_counts.values, color='#2ecc71')
ax1.set_xticks(range(len(cash_counts)))
ax1.set_xticklabels(cash_counts.index)
ax1.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax1.set_title('Cash Prizes Distribution', fontsize=14, fontweight='bold')

for i, (bar, value) in enumerate(zip(bars1, cash_counts.values)):
    ax1.text(i, value + 10, str(value), ha='center', fontweight='bold')

# Other prizes distribution
other_data = df[df['other_prizes_count'] > 0]['other_prizes_count']
other_bins = [0, 1, 3, 5, 10, max(other_data) + 1]
other_labels = ['1', '2-3', '4-5', '6-10', '>10']
other_binned = pd.cut(other_data, bins=other_bins, labels=other_labels, include_lowest=True)
other_counts = other_binned.value_counts().sort_index()

bars2 = ax2.bar(range(len(other_counts)), other_counts.values, color='#e67e22')
ax2.set_xticks(range(len(other_counts)))
ax2.set_xticklabels(other_counts.index)
ax2.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax2.set_title('Other Prizes Distribution', fontsize=14, fontweight='bold')

for i, (bar, value) in enumerate(zip(bars2, other_counts.values)):
    ax2.text(i, value + 5, str(value), ha='center', fontweight='bold')

plt.suptitle('Prize Types Comparison', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('charts/08_prize_types_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 9: Winners Announced Status
print("9. Generating winners announced status chart...")
fig, ax = plt.subplots(figsize=(10, 6))
winners_counts = df['winners_announced'].value_counts()
colors = ['#3498db', '#f39c12']
labels = ['Winners Not Announced' if not x else 'Winners Announced' for x in winners_counts.index]
bars = ax.bar(range(len(winners_counts)), winners_counts.values, color=colors[:len(winners_counts)])
ax.set_xticks(range(len(winners_counts)))
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Hackathons by Winner Announcement Status', fontsize=16, fontweight='bold', pad=20)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, winners_counts.values)):
    percentage = (value / len(df)) * 100
    ax.text(i, value + 100, f'{value:,}\n({percentage:.1f}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/09_winners_announced.png', dpi=300, bbox_inches='tight')
plt.close()

# Chart 10: Managed by Devpost vs Community
print("10. Generating management type chart...")
fig, ax = plt.subplots(figsize=(10, 6))
managed_counts = df['managed_by_devpost'].value_counts()
colors = ['#c0392b', '#16a085']
labels = ['Community Managed' if not x else 'Managed by Devpost' for x in managed_counts.index]
bars = ax.bar(range(len(managed_counts)), managed_counts.values, color=colors[:len(managed_counts)])
ax.set_xticks(range(len(managed_counts)))
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel('Number of Hackathons', fontsize=12, fontweight='bold')
ax.set_title('Hackathons by Management Type', fontsize=16, fontweight='bold', pad=20)

# Add value labels on top of bars
for i, (bar, value) in enumerate(zip(bars, managed_counts.values)):
    percentage = (value / len(df)) * 100
    ax.text(i, value + 100, f'{value:,}\n({percentage:.1f}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/10_management_type.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n✅ All charts generated successfully in 'charts/' directory!")

# Generate summary statistics
print("\n" + "="*60)
print("DATA INSIGHTS SUMMARY")
print("="*60)

print(f"\n📊 Total Hackathons: {len(df):,}")
print(f"🟢 Open: {len(df[df['open_state'] == 'open']):,}")
print(f"🔴 Closed: {len(df[df['open_state'] == 'closed']):,}")

print(f"\n💰 Prize Statistics:")
prizes_with_value = df[df['prize_numeric'] > 0]
print(f"   Hackathons with prizes: {len(prizes_with_value):,}")
print(f"   Average prize: ${prizes_with_value['prize_numeric'].mean():,.0f}")
print(f"   Median prize: ${prizes_with_value['prize_numeric'].median():,.0f}")
print(f"   Highest prize: ${prizes_with_value['prize_numeric'].max():,.0f}")

print(f"\n👥 Registration Statistics:")
reg_with_value = df[df['registrations_count'] > 0]
print(f"   Hackathons with registrations: {len(reg_with_value):,}")
print(f"   Average registrations: {reg_with_value['registrations_count'].mean():,.0f}")
print(f"   Median registrations: {reg_with_value['registrations_count'].median():,.0f}")
print(f"   Highest registrations: {reg_with_value['registrations_count'].max():,.0f}")

print(f"\n🏆 Top 3 Organizations:")
for i, (org, count) in enumerate(df['organization_name'].value_counts().head(3).items(), 1):
    print(f"   {i}. {org}: {count} hackathons")

print(f"\n🎯 Top 3 Themes:")
theme_counts = Counter(all_themes).most_common(3)
for i, (theme, count) in enumerate(theme_counts, 1):
    print(f"   {i}. {theme}: {count} hackathons")

print(f"\n🌍 Top 3 Locations:")
for i, (loc, count) in enumerate(df['location'].value_counts().head(3).items(), 1):
    print(f"   {i}. {loc}: {count} hackathons")

print(f"\n⭐ Featured: {len(df[df['featured'] == True]):,} ({len(df[df['featured'] == True])/len(df)*100:.1f}%)")
print(f"🏅 Winners Announced: {len(df[df['winners_announced'] == True]):,} ({len(df[df['winners_announced'] == True])/len(df)*100:.1f}%)")
print(f"🛡️  Managed by Devpost: {len(df[df['managed_by_devpost'] == True]):,} ({len(df[df['managed_by_devpost'] == True])/len(df)*100:.1f}%)")

print("\n" + "="*60)
