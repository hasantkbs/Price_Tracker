import SwiftUI

struct ProductRowView: View {
    let product: Product

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top) {
                Text(product.displayName)
                    .font(.headline)
                    .lineLimit(2)
                Spacer()
                HStack(spacing: 4) {
                    if product.isAlertEnabled {
                        Image(systemName: "bell.fill")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                    if product.isTargetReached {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                }
            }

            HStack(spacing: 20) {
                priceColumn(label: "Mevcut", value: product.currentPrice, color: currentPriceColor)
                priceColumn(label: "Hedef",  value: product.targetPrice,  color: .blue)
                if let alert = product.alertPrice {
                    priceColumn(label: "Alarm", value: alert, color: .orange)
                }
                Spacer()
                if let change = product.priceChangePercent {
                    changeBadge(change)
                }
            }

            if let date = product.lastCheckedAt {
                Text("Son kontrol: \(shortDate(date))")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private func priceColumn(label: String, value: Double?, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label).font(.caption2).foregroundColor(.secondary)
            if let v = value {
                Text(String(format: "%.2f ₺", v))
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(color)
            } else {
                Text("—").font(.subheadline).foregroundColor(.secondary)
            }
        }
    }

    @ViewBuilder
    private func changeBadge(_ change: Double) -> some View {
        let isDown = change < 0
        Text(String(format: "%+.1f%%", change))
            .font(.caption)
            .fontWeight(.semibold)
            .foregroundColor(isDown ? .green : .red)
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(
                RoundedRectangle(cornerRadius: 5)
                    .fill((isDown ? Color.green : Color.red).opacity(0.12))
            )
    }

    private var currentPriceColor: Color {
        guard let current = product.currentPrice else { return .primary }
        return current <= product.targetPrice ? .green : .primary
    }

    private func shortDate(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "dd.MM.yyyy HH:mm"
        return f.string(from: date)
    }
}
