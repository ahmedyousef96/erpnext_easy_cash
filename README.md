# Easy Cash

Simplified cash in/out for non-accounting staff using ERPNext.

## Features

- **Treasury Management** — Define cash boxes and bank accounts as treasury sources
- **Easy Cash Categories** — Categorize transactions (e.g., Administrative Expenses, Sales Revenue)
- **Quick Cash In/Out** — Record transactions in seconds with direct submit, no approval workflow needed
- **Automatic GL Entries** — Posts to General Ledger behind the scenes using standard ERPNext accounting patterns
- **Cash Voucher Print Format** — Professional receipt with letterhead, amount in words, and signature block
- **Easy Cash Entry Register** — Tree-structured report with expandable category detail rows
- **Category Summary Report** — Grouped summary by category with bar chart dashboard visualization
- **Accounting Dimensions** — Full support for cost center, branch, project, and custom dimensions
- **Multi-Company** — Works across multiple companies with per-company categories and treasuries

## Requirements

- Frappe Framework >= 15.x
- ERPNext >= 15.x

## Installation

See [INSTALL.md](INSTALL.md) for installation instructions.

## Usage

1. Create **Treasury** records for each cash box or bank account
2. Create **Easy Cash Categories** (e.g., "Administrative Expenses" for Cash Out, "Sales Revenue" for Cash In)
3. Create **Easy Cash Entry** — select Cash In or Cash Out, pick a category, enter amount, and submit
4. View the auto-generated GL entries via the "View General Ledger" button

## Author

**Ahmed Yousef**
- WhatsApp: +201028171836
- Email: Ay716881@gmail.com
- GitHub: [ahmedyousef96](https://github.com/ahmedyousef96)

## License

MIT
