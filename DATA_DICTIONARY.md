# Data Dictionary

Tài liệu này mô tả ý nghĩa các cột trong:
- `data/processed/master_dataset_h4_cleaned_v1.csv` (dataset gốc đã làm sạch)
- `data/processed/final.csv` (dataset feature-engineering/target)

Ghi chú:
- Một số cột on-chain/news phụ thuộc nhà cung cấp dữ liệu và pipeline xử lý; mô tả dưới đây theo ý nghĩa phổ biến nhất.
- Dataset H4: mỗi dòng thường đại diện cho 1 cây nến 4 giờ (nếu pipeline của bạn đúng theo tên file).

## 1) `master_dataset_h4_cleaned_v1.csv`

| Column | Ý nghĩa |
|---|---|
| `timestamp` | Mốc thời gian của kỳ (timestamp của nến). |
| `BTC_open` | Giá mở cửa BTC trong kỳ. |
| `BTC_high` | Giá cao nhất BTC trong kỳ. |
| `BTC_low` | Giá thấp nhất BTC trong kỳ. |
| `BTC_close` | Giá đóng cửa BTC trong kỳ. |
| `BTC_volume` | Khối lượng giao dịch BTC (base volume). |
| `BTC_quote_volume` | Khối lượng giao dịch BTC theo đồng định giá (quote volume, thường là USD/USDT). |
| `BTC_trades` | Số lượng trade/khớp lệnh BTC trong kỳ. |
| `ETH_open` | Giá mở cửa ETH trong kỳ. |
| `ETH_high` | Giá cao nhất ETH trong kỳ. |
| `ETH_low` | Giá thấp nhất ETH trong kỳ. |
| `ETH_close` | Giá đóng cửa ETH trong kỳ. |
| `ETH_volume` | Khối lượng giao dịch ETH (base volume). |
| `ETH_quote_volume` | Khối lượng giao dịch ETH theo đồng định giá (quote volume). |
| `ETH_trades` | Số lượng trade/khớp lệnh ETH trong kỳ. |
| `BTC_market_cap` | Vốn hoá thị trường BTC tại thời điểm đó. |
| `ETH_market_cap` | Vốn hoá thị trường ETH tại thời điểm đó. |
| `USDT_market_cap` | Vốn hoá USDT (xấp xỉ tổng cung do giá thường ~1). |
| `USDC_market_cap` | Vốn hoá USDC (xấp xỉ tổng cung do giá thường ~1). |
| `BTC_active_addresses` | Số địa chỉ BTC hoạt động (thường: có gửi/nhận on-chain) trong kỳ. |
| `BTC_tx_count` | Số lượng giao dịch BTC on-chain trong kỳ. |
| `ETH_active_addresses` | Số địa chỉ ETH hoạt động trong kỳ. |
| `ETH_tx_count` | Số lượng giao dịch ETH on-chain trong kỳ. |
| `mining_difficulty` | Độ khó đào (BTC). |
| `hash_rate_ths` | Hashrate mạng (đơn vị TH/s). |
| `miner_revenue_usd` | Doanh thu thợ đào (USD) trong kỳ (thường gồm block reward + fee). |
| `BTC_onchain_total_supply` | Tổng cung BTC on-chain (circulating/issued supply tuỳ nguồn). |
| `BTC_onchain_mvrv_ratio` | MVRV = Market Value / Realized Value (chỉ báo định giá on-chain). |
| `BTC_onchain_exchange_inflow_native` | Lượng BTC nạp lên sàn (exchange inflow) tính theo BTC. |
| `BTC_onchain_exchange_inflow_usd` | Exchange inflow quy đổi USD. |
| `BTC_onchain_exchange_outflow_native` | Lượng BTC rút khỏi sàn (exchange outflow) tính theo BTC. |
| `BTC_onchain_exchange_outflow_usd` | Exchange outflow quy đổi USD. |
| `BTC_onchain_exchange_supply_native` | Số dư BTC nằm trên ví sàn (BTC). |
| `BTC_onchain_exchange_supply_usd` | Số dư BTC trên sàn quy đổi USD. |
| `news_article_count` | Số bài tin tức thu thập được trong kỳ. |
| `news_log_article_count` | Log-transform của số bài (thường là `log(1 + count)` để giảm lệch). |
| `has_news` | Cờ 0/1: trong kỳ có tin hay không. |
| `news_combined_sent_mean` | Trung bình sentiment tổng hợp của tin trong kỳ. |
| `news_combined_sent_std` | Độ lệch chuẩn sentiment tổng hợp. |
| `news_combined_sent_max` | Sentiment tổng hợp lớn nhất. |
| `news_combined_sent_min` | Sentiment tổng hợp nhỏ nhất. |
| `news_combined_sent_max_abs` | Trị tuyệt đối lớn nhất của sentiment (mức “cực đoan” mạnh nhất). |
| `news_combined_sent_sum_abs` | Tổng trị tuyệt đối sentiment (tổng “cường độ” cảm xúc). |
| `news_bull_ratio` | Tỷ lệ tin bullish (tích cực) trong kỳ. |
| `news_bear_ratio` | Tỷ lệ tin bearish (tiêu cực) trong kỳ. |
| `news_p_bull_mean` | Trung bình xác suất tin là bullish (từ model phân loại). |
| `news_p_bear_mean` | Trung bình xác suất tin là bearish. |
| `news_p_neu_mean` | Trung bình xác suất tin là neutral. |
| `news_max_p_bull_bucket` | Bucket/nhãn theo mức `p_bull` lớn nhất (thường là khoảng xác suất). |
| `news_max_p_bear_bucket` | Bucket/nhãn theo mức `p_bear` lớn nhất (thường là khoảng xác suất). |
| `news_is_conflict` | Cờ 0/1: tín hiệu tin mâu thuẫn/phân tán (ví dụ vừa bull vừa bear mạnh). |
| `news_head_sent_mean` | Trung bình sentiment tính riêng trên tiêu đề (headline). |
| `news_head_sent_std` | Độ lệch chuẩn sentiment headline. |
| `news_head_sent_max` | Sentiment headline lớn nhất. |
| `news_head_sent_min` | Sentiment headline nhỏ nhất. |
| `news_head_global_diff_mean` | Trung bình chênh lệch giữa sentiment headline và sentiment nội dung/“global” (tuỳ pipeline). |
| `news_head_global_abs_diff_mean` | Trung bình trị tuyệt đối chênh lệch headline vs global. |
| `news_head_exag_ratio` | Tỷ lệ “giật tít”: headline cực đoan hơn nội dung (thường dựa trên diff/abs diff). |
| `sentiment_index_value` | Giá trị chỉ số sentiment tổng hợp (index riêng của bạn/nguồn). |
| `sentiment_index_classification` | Phân loại từ chỉ số sentiment (ví dụ: Fear/Neutral/Greed hoặc Bear/Neutral/Bull). |

## 2) `final.csv`

| Column | Ý nghĩa |
|---|---|
| `timestamp` | Mốc thời gian tương ứng với hàng feature. |
| `BTC_log_return` | Log return BTC: `ln(C_t / C_{t-1})` (thường dùng giá đóng cửa). |
| `ETH_log_return` | Log return ETH: `ln(C_t / C_{t-1})`. |
| `target` | Biến mục tiêu dự báo (thường là return/giá tương lai theo horizon trong pipeline). |
| `BTC_vol_log_return` | Volatility của `BTC_log_return` (thường là rolling std; đôi khi là log-vol). |
| `log_rvol` | Log của realized volatility (volatility thực đo từ rolling returns). |
| `vol_gk` | Volatility Garman–Klass (ước lượng biến động dựa trên OHLC). |
| `vol_gk_z` | Z-score của `vol_gk` (chuẩn hoá theo rolling mean/std). |
| `vol_signed` | Volatility có dấu (thường gắn dấu theo hướng return để phân biệt tăng/giảm). |
| `clv` | Close Location Value: vị trí giá đóng trong biên độ nến (thường được chuẩn hoá về [-1, 1]). |
| `wick_imbalance` | Mất cân bằng râu nến (upper wick vs lower wick), đại diện áp lực mua/bán. |
| `bb_pct_b` | Bollinger %B: vị trí giá so với dải Bollinger (0–1, có thể vượt biên). |
| `bb_width` | Độ rộng dải Bollinger (đại diện mức biến động). |
| `btc_eth_corr` | Tương quan trượt (rolling correlation) giữa return BTC và ETH. |
| `log_rel_ats` | Log “relative average trade size” (thường dựa trên `quote_volume / trades`, có thể là tỉ lệ tương đối). |
| `stable_supply_change` | Thay đổi cung stablecoin (thường từ `USDT_market_cap`/`USDC_market_cap` hoặc tổng). |
| `ssr_z_score` | Z-score Stablecoin Supply Ratio (SSR thường là vốn hoá BTC / vốn hoá stablecoin). |
| `usdt_dom_change` | Thay đổi “USDT dominance” (tỷ trọng USDT trong tổng market hoặc trong nhóm stablecoin). |
| `addr_log_growth` | Tăng trưởng log của active addresses (thường: `ln(A_t/A_{t-1})`). |
| `intensity_change` | Thay đổi cường độ hoạt động mạng (thường dựa trên tx_count hoặc tx/addr). |
| `network_valuation_z` | Z-score chỉ báo định giá mạng (thường là NVT hoặc biến thể). |
| `hash_ribbon_spread` | Chênh lệch Hash Ribbon (thường: MA ngắn hạn hashrate − MA dài hạn). |
| `log_puell` | Log của Puell Multiple (doanh thu thợ đào / MA dài hạn doanh thu). |
| `onchain_mvrv_z` | Z-score của MVRV (chuẩn hoá theo rolling). |
| `onchain_netflow_z` | Z-score netflow sàn (inflow − outflow), chuẩn hoá. |
| `reserve_ratio_change` | Thay đổi “reserve ratio” (tuỳ định nghĩa on-chain/pipeline). |
| `news_article_count` | Số bài tin trong kỳ (đưa vào trực tiếp như feature). |
| `news_impact_score` | Điểm “tác động tin” tổng hợp (thường kết hợp số lượng tin + mức độ sentiment + trọng số). |
| `news_sentiment_decay_slow` | Sentiment đã làm mượt/giảm dần theo thời gian (EMA/decay chậm). |
| `news_sentiment_shock` | “Cú sốc” sentiment: thay đổi đột ngột so với baseline/decay. |
| `fng_change` | Thay đổi Fear & Greed Index (nếu có nguồn FNG). |
| `fng_divergence` | Độ phân kỳ giữa FNG và giá/return (hoặc giữa FNG và baseline; tuỳ pipeline). |

