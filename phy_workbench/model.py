from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChildNode:
    node_id: str
    title: str
    subtitle: str
    formula: str


@dataclass(frozen=True)
class GroupNode:
    group_id: str
    title: str
    subtitle: str
    color: str
    children: tuple[ChildNode, ...]


SYSTEM_GRAPH = (
    GroupNode("source", "Source", "", "#555555", (
        ChildNode("source", "Payload bits", "Random bits or UTF-8 payload", "bᵢ ∈ {0,1}"),
        ChildNode("group", "Bit framing", "Padding and modulation-word grouping", "Bₖ=[bₖq,…,bₖq+q−1]"),
        ChildNode("transport_block", "Transport block", "CRC attachment and TB preparation", "a = CRC(TB)"),
    )),
    GroupNode("tx_coding", "TX Coding", "", "#555555", (
        ChildNode("cb_segment", "CB segmentation", "Split a transport block into code blocks", "TB → {CB₁,…,CB_C}"),
        ChildNode("ldpc_encode", "5G NR LDPC", "Base-graph selection and LDPC encoding", "c = G·u mod 2"),
        ChildNode("rate_match", "Rate matching", "Puncturing, shortening and repetition", "c → e, |e|=E"),
        ChildNode("scramble", "Scrambling", "Cell/user-dependent binary scrambling", "b̃ = b ⊕ s"),
    )),
    GroupNode("tx_waveform", "TX Waveform", "", "#555555", (
        ChildNode("mapper", "M-QAM mapper", "BPSK, QPSK and 16-QAM mapping", "xₖ = ℳ(Bₖ)"),
        ChildNode("layer_map", "Layer mapping", "Map symbols onto spatial layers", "x → x⁽ˡ⁾"),
        ChildNode("resource_grid", "Resource grid", "Place data and DM-RS on resources", "x → X[k,l]"),
        ChildNode("precoding", "Precoding", "Map layers onto transmit antennas", "Xₚ = W·X"),
        ChildNode("ofdm_mod", "CP-OFDM", "IFFT and cyclic-prefix insertion", "s[n]=IFFT{X[k]}+CP"),
    )),
    GroupNode("channel", "Channel", "", "#555555", (
        ChildNode("channel", "AWGN", "Complex additive white Gaussian noise", "y=x+n"),
        ChildNode("path_loss", "Large-scale loss", "Path loss and shadow fading", "Pᵣ=Pₜ−PL−SF"),
        ChildNode("multipath", "TDL/CDL fading", "3GPP frequency-selective multipath", "y=h*x+n"),
        ChildNode("doppler", "Mobility", "Doppler and temporal channel variation", "f_D=v f_c/c"),
        ChildNode("impairments", "RF impairments", "CFO, phase noise and nonlinear distortion", "y=g(x;θ_RF)+n"),
    )),
    GroupNode("rx_waveform", "RX Waveform", "", "#555555", (
        ChildNode("synchronization", "Synchronization", "Timing and carrier-frequency synchronization", "ŷ[n]=y[n−τ]e^{-j2πΔfn}"),
        ChildNode("ofdm_demod", "OFDM demodulation", "Remove CP and apply FFT", "Y[k]=FFT{y[n]}"),
        ChildNode("channel_est", "Channel estimation", "DM-RS based LS/LMMSE estimation", "Ĥ=Yₚ/Xₚ"),
        ChildNode("equalizer", "Equalization", "SISO or MIMO LMMSE equalization", "x̂=(HᴴH+σ²I)⁻¹Hᴴy"),
        ChildNode("detector", "Soft detector", "Symbol detection and soft-bit generation", "LLR(bᵢ|y)"),
    )),
    GroupNode("rx_coding", "RX Decoding", "", "#555555", (
        ChildNode("descramble", "Descrambling", "Reverse transmitter scrambling", "b̂ = b̃ ⊕ s"),
        ChildNode("rate_recover", "Rate recovery", "Reverse rate matching and combine redundancy", "e → LLR(c)"),
        ChildNode("ldpc_decode", "LDPC decoding", "Iterative belief-propagation decoding", "û = LDPCDecode(LLR,I)"),
        ChildNode("crc_harq", "CRC / HARQ", "Validate block and generate ACK/NACK", "ACK = CRC(û)"),
    )),
    GroupNode("metrics", "Metrics", "", "#555555", (
        ChildNode("sink", "BER / BLER", "Compare transmitted and recovered information", "BER=(1/N)Σ𝟙[bᵢ≠b̂ᵢ]"),
        ChildNode("goodput", "Goodput", "Successfully delivered information per unit time", "G=R·(1−BLER)"),
        ChildNode("runtime", "Runtime", "Processing latency and decoder complexity", "T=T_TX+T_RX"),
        ChildNode("policy_log", "Policy trace", "Selected MCS and constraint violations", "{sₜ,aₜ,rₜ}"),
    )),
    GroupNode("adaptation", "Adaptation", "", "#555555", (
        ChildNode("channel_state", "Channel state", "Estimated SINR, CSI quality and Doppler", "sₜ=[SINR,σ²_CSI,f_D,…]"),
        ChildNode("feedback", "Feedback history", "CQI and recent ACK/NACK observations", "hₜ={CQI,ACK/NACK}"),
        ChildNode("policy", "Policy", "Lookup table, rules or a learned model", "aₜ=π(sₜ,hₜ,qₜ)"),
        ChildNode("mcs_select", "MCS selection", "Choose modulation and LDPC coding rate", "a_MCS=(M,R_c)"),
        ChildNode("complexity_select", "Complexity control", "Choose decoder iterations and receiver budget", "a_C=(I_dec,T_budget)"),
    )),
)

IMPLEMENTED_NODES = {"source", "group", "mapper", "channel", "detector", "sink"}
LEVEL0_GRAPH = SYSTEM_GRAPH


# Hệ quy chiếu lý thuyết & Chỉ dẫn Debug chi tiết cho từng khối trong hệ thống
NODE_THEORY_NOTES: dict[str, str] = {
    # 1. NHÓM SOURCE (Nguồn phát)
    "source": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Tạo luồng bit nhị phân độc lập phân phối đều (i.i.d bits) hoặc chuỗi ký tự UTF-8 (8 bits/byte).\n"
        "• Công thức: bᵢ ∈ {0, 1}, P(bᵢ=0) = P(bᵢ=1) = 0.5.\n"
        "• Thực tế phần cứng: Tương đương thanh ghi dịch phản hồi tuyến tính LFSR (chuỗi PRBS9, PRBS15) hoặc gói tin IP từ tầng MAC.\n"
        "• Chỉ dẫn Debug: Tổng số bit N > 0; tỉ lệ bit 0 và 1 xấp xỉ 50% để tránh độ lệch DC (DC bias)."
    ),
    "group": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Bộ chuyển đổi Nối tiếp sang Song song (Serial-to-Parallel). Gom q = log₂(M) bit liên tiếp thành 1 từ mã symbol.\n"
        "• Công thức: Bₖ = [b_kq, b_kq+1, ..., b_kq+q-1] với q = 1 (BPSK), q = 2 (QPSK), q = 4 (16-QAM).\n"
        "• Thực tế phần cứng: Dùng bộ đệm S/P Buffer; chèn zero-padding ở cuối nếu tổng bit không chia hết cho q.\n"
        "• Chỉ dẫn Debug: Số lượng symbol N_s = ceil(N/q); giá trị index từ mã nằm trong đoạn [0, M-1]."
    ),
    "transport_block": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Đóng gói khối truyền tải Transport Block (TB) và gắn mã kiểm tra dư thừa tuần hoàn CRC-24A/24B (3GPP TS 38.212).\n"
        "• Công thức: a = CRC(TB), đa thức sinh g_CRC24A(D) = D²⁴ + D²³ + D¹⁸ + D¹⁷ + D¹⁴ + D¹¹ + D¹⁰ + D⁷ + D⁶ + D⁵ + D⁴ + D³ + D + 1.\n"
        "• Thực tế phần cứng: Mạch chia đa thức dùng thanh ghi dịch để phát hiện lỗi khung ở bên thu.\n"
        "• Chỉ dẫn Debug: Bên thu chia đa thức nhận được cho g(D), nếu phần dư = 0 thì không có lỗi."
    ),

    # 2. NHÓM TX CODING (Mã hóa kênh phát)
    "cb_segment": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Phân đoạn khối truyền tải lớn (TB > 3824 bit) thành nhiều khối mã nhỏ (Code Blocks - CB) để giải mã song song.\n"
        "• Công thức: TB → {CB₁, CB₂, ..., CB_C}.\n"
        "• Thực tế phần cứng: Chuẩn 5G NR quy định kích thước cực đại K_cb = 8448 bit (BG1) hoặc 3840 bit (BG2).\n"
        "• Chỉ dẫn Debug: Mỗi CB được gán thêm mã CRC-24B riêng để kiểm tra lỗi từng phần."
    ),
    "ldpc_encode": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Mã hóa kiểm soát lỗi kênh truyền LDPC (Low-Density Parity-Check) chuẩn 5G NR theo Base Graph 1 hoặc Base Graph 2.\n"
        "• Công thức: c = G · u mod 2; ma trận kiểm tra chẵn lẻ thỏa mãn H · cᵀ = 0.\n"
        "• Thực tế phần cứng: Ma trận bán tuần hoàn (Quasi-Cyclic LDPC) cho phép kiến trúc mã hóa phần cứng dạng thanh ghi dịch tốc độ cao.\n"
        "• Chỉ dẫn Debug: Tỉ lệ mã R_c = K / N_cb; kiểm tra tính chẵn lẻ H · cᵀ ≡ 0 (mod 2)."
    ),
    "rate_match": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Đệm vòng tròn (Circular Buffer), chọc lỗ (puncturing), cắt ngắn (shortening) và lặp bit (repetition) để khớp dung lượng tài nguyên.\n"
        "• Công thức: c → e, độ dài |e| = E.\n"
        "• Thực tế phần cứng: Điều chỉnh số lượng bit mã phát ra đúng bằng số Resource Elements (RE) được cấp phát × q.\n"
        "• Chỉ dẫn Debug: E > N_cb là chế độ lặp lại (repetition); E < N_cb là chế độ chọc lỗ (puncturing)."
    ),
    "scramble": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Phép XOR bit với chuỗi giả ngẫu nhiên Gold sequence chiều dài 31 phụ thuộc Cell ID (N_ID_cell) và RNTI (3GPP TS 38.211).\n"
        "• Công thức: b̃(i) = (b(i) + c(i)) mod 2.\n"
        "• Thực tế phần cứng: Khử tương quan tín hiệu giữa các trạm liền kề và chống xuất hiện chuỗi '0' hoặc '1' liên tục gây méo phổ.\n"
        "• Chỉ dẫn Debug: Tính chất tự nghịch đảo: b̃ ⊕ c = b (giải xáo trộn dùng cùng chuỗi c)."
    ),

    # 3. NHÓM TX WAVEFORM (Điều chế & Dạng sóng phát)
    "mapper": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Ánh xạ từ mã nhị phân sang tọa độ chòm sao phức I + jQ theo mã Gray và chuẩn hóa năng lượng trung bình E_s = 1 (3GPP TS 38.211).\n"
        "• Công thức:\n"
        "  - BPSK: x = ±1 (E_s = 1)\n"
        "  - QPSK: x = (±1 ± j) / √2 (E_s = 1)\n"
        "  - 16-QAM: x = (I + jQ) / √10 với I, Q ∈ {±1, ±3} (E_s = 1)\n"
        "• Thực tế phần cứng: Bảng tra cứu LUT (Look-Up Table) trong chip FPGA ánh xạ 4 bit → 16 điểm tọa độ IQ.\n"
        "• Chỉ dẫn Debug: Công suất trung bình E[|xₖ|²] = 1.0 ± 0.01; hai điểm lân cận chỉ lệch nhau đúng 1 bit (Gray coding)."
    ),
    "layer_map": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Phân phối chuỗi symbol điều chế lên v luồng không gian (Spatial Layers) phục vụ truyền dẫn MIMO đa ăng-ten.\n"
        "• Công thức: x → x⁽ˡ⁾ với l = 0, 1, ..., v-1.\n"
        "• Thực tế phần cứng: Tăng thông lượng dữ liệu gấp v lần mà không cần mở rộng băng thông tần số.\n"
        "• Chỉ dẫn Debug: Số symbol trên mỗi layer = Tổng số symbol / v."
    ),
    "resource_grid": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Xếp symbol dữ liệu và pilot dẫn đường (DM-RS, PT-RS) lên lưới tài nguyên Resource Grid (Tần số × Thời gian).\n"
        "• Công thức: X[k, l] tại sóng mang con k và symbol thời gian l.\n"
        "• Thực tế phần cứng: 1 Resource Block (RB) = 12 sóng mang con liên tiếp trong 1 khe thời gian (slot).\n"
        "• Chỉ dẫn Debug: Không để dữ liệu đè lên vị trí của pilot DM-RS hoặc sóng mang DC."
    ),
    "precoding": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Nhân ma trận trọng số phát W để định hình búp sóng (Beamforming) và ghép từ v layer sang P cổng ăng-ten vật lý.\n"
        "• Công thức: X_p = W · X.\n"
        "• Thực tế phần cứng: Hướng năng lượng phát về phía người dùng, tăng tỉ số SINR và giảm can nhiễu đa người dùng.\n"
        "• Chỉ dẫn Debug: Ma trận W chuẩn hóa công suất phát Tr(W Wᴴ) = v."
    ),
    "ofdm_mod": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Biến đổi ngược IFFT từ miền tần số sang miền thời gian và chèn tiền tố lặp Cyclic Prefix (CP).\n"
        "• Công thức: s[n] = IFFT{X[k]} + CP.\n"
        "• Thực tế phần cứng: CP biến phép chập tuyến tính của kênh đa đường thành phép chập vòng, giúp cân bằng kênh ở bên thu đơn giản (1-tap equalizer).\n"
        "• Chỉ dẫn Debug: Độ dài tiền tố lặp N_CP phải lớn hơn độ trễ cực đại của kênh đa đường (N_CP > τ_max)."
    ),

    # 4. NHÓM CHANNEL (Kênh truyền vô tuyến)
    "channel": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Mô hình tạp âm nhiệt nội tại trong máy thu bằng nhiễu trắng Gauss phức đối xứng tròn n ~ CN(0, N₀).\n"
        "• Công thức: y = x + n;\n"
        "  - Năng lượng bit: E_b = E_s / q = 1 / q (với E_s = 1)\n"
        "  - Mật độ tạp âm: N₀ = (1/q) / 10^(EbN0_dB / 10)\n"
        "  - Độ lệch chuẩn mỗi nhánh: σ = √(N₀ / 2)\n"
        "• Thực tế phần cứng: Mô hình hóa giới hạn lý thuyết kênh Shannon lý tưởng.\n"
        "• Chỉ dẫn Debug: Phương sai thực nghiệm Var(n) ≈ N₀; phần thực và phần ảo độc lập thống kê với nhau."
    ),
    "path_loss": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Suy giảm công suất tín hiệu theo khoảng cách địa lý d và che khuất bởi địa hình/tòa nhà (Log-normal Shadowing).\n"
        "• Công thức: P_r = P_t - PL(d) - SF; PL(d) = 20log₁₀(4πd/λ) + 10α·log₁₀(d/d₀).\n"
        "• Thực tế phần cứng: Xác định vùng phủ sóng (coverage) và suy hao suy giảm từ 20 đến 40 dB/decade.\n"
        "• Chỉ dẫn Debug: Khoảng cách tăng gấp đôi → công suất giảm khoảng 6 dB (trong không gian tự do, α=2)."
    ),
    "multipath": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Hiện tượng phản xạ/tán xạ tạo nhiều tia sóng tới máy thu với biên độ và trễ khác nhau (Rayleigh / Rician Fading, chuẩn 3GPP TR 38.901 TDL/CDL).\n"
        "• Công thức: y(t) = ∑ aᵢ(t) x(t - τᵢ) + n(t) ↔ Y[k] = H[k] X[k] + N[k].\n"
        "• Thực tế phần cứng: Gây hiện tượng fading chọn lọc tần số (Frequency-selective fading) với các điểm lõm sâu (deep nulls) trên phổ.\n"
        "• Chỉ dẫn Debug: Khoảng trễ phân tán RMS Delay Spread quyết định băng thông kết hợp B_c ≈ 1 / (5·τ_rms)."
    ),
    "doppler": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Sự di chuyển tương đối giữa trạm phát và máy thu gây dịch tần số Doppler f_D = (v / c) · f_c · cos(θ).\n"
        "• Công thức: Thời gian kết hợp T_c ≈ 9 / (16π·f_D).\n"
        "• Thực tế phần cứng: Tốc độ di chuyển càng cao (tàu cao tốc, ô tô) thì pha của kênh thay đổi càng nhanh giữa các symbol liên tiếp.\n"
        "• Chỉ dẫn Debug: f_D lớn đòi hỏi khoảng cách giữa các pilot DM-RS trong miền thời gian phải dày hơn."
    ),
    "impairments": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Phi lý tưởng phần cứng vô tuyến RF: mất cân bằng IQ (IQ Imbalance), trôi tần số sóng mang (CFO), nhiễu pha (Phase Noise) và méo phi tuyến của bộ khuếch đại PA.\n"
        "• Công thức: y = g(x; θ_RF) + n.\n"
        "• Thực tế phần cứng: CFO làm xoay toàn bộ chòm sao IQ theo thời gian; PA làm bão hòa co cụm các điểm biên ngoài của 16-QAM/64-QAM.\n"
        "• Chỉ dẫn Debug: Đánh giá bằng đại lượng EVM (Error Vector Magnitude) chuẩn 3GPP (EVM < 3.5% cho 64-QAM)."
    ),

    # 5. NHÓM RX WAVEFORM (Dạng sóng & Giải điều chế thu)
    "synchronization": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Tìm điểm bắt đầu khung (Timing Synchronization) và bù sai lệch tần số sóng mang (CFO Estimation) dựa trên chuỗi PSS/SSS.\n"
        "• Công thức: ŷ[n] = y[n - τ̂] · e^(-j 2π Δf̂ n).\n"
        "• Thực tế phần cứng: Tương quan chéo (Cross-correlation) với chuỗi mẫu để tìm đỉnh tương quan thời gian và góc lệch pha.\n"
        "• Chỉ dẫn Debug: Sai số tần số dư sau đồng bộ phải nhỏ hơn 1% khoảng cách sóng mang con (Δf_scs)."
    ),
    "ofdm_demod": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Cắt bỏ tiền tố lặp CP và thực hiện biến đổi thuận FFT để đưa tín hiệu thời gian về từng sóng mang con miền tần số.\n"
        "• Công thức: Y[k] = FFT{y[n]}.\n"
        "• Thực tế phần cứng: Khôi phục lại dữ liệu song song trên toàn bộ sóng mang con không bị can nhiễu ISI.\n"
        "• Chỉ dẫn Debug: Kích thước FFT N_FFT (128, 512, 1024, 2048, 4096) phải khớp hoàn toàn với bên phát."
    ),
    "channel_est": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Sử dụng pilot DM-RS đã biết để tính ma trận đáp ứng kênh Ĥ bằng thuật toán Bình phương tối thiểu (LS) hoặc LMMSE.\n"
        "• Công thức: Ĥ_LS = Y_p / X_p; Ĥ_LMMSE = R_HH · (R_HH + σ²(X_p X_pᴴ)⁻¹)⁻¹ · Ĥ_LS.\n"
        "• Thực tế phần cứng: Nội suy 2D (Thời gian - Tần số) để có đáp ứng kênh tại mọi vị trí Resource Element.\n"
        "• Chỉ dẫn Debug: Sai số chuẩn hóa NMSE của ước lượng kênh phải giảm khi SNR tăng."
    ),
    "equalizer": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Khử méo pha-đinh và tách luồng MIMO bằng bộ cân bằng Zero-Forcing (ZF) hoặc LMMSE.\n"
        "• Công thức: x̂ = (Hᴴ H + σ² I)⁻¹ Hᴴ y.\n"
        "• Thực tế phần cứng: Ở SNR cao, LMMSE tiệm cận ZF; ở SNR thấp, LMMSE tránh khuếch đại nhiễu hiệu quả hơn ZF.\n"
        "• Chỉ dẫn Debug: Điểm chòm sao sau cân bằng phải co cụm rõ nét quanh các điểm chòm sao lý thuyết."
    ),
    "detector": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Bộ tách sóng tối ưu theo khoảng cách Euclid cực tiểu (Maximum Likelihood - ML) hoặc tính tỉ số Log-Likelihood Ratio (LLR) mềm.\n"
        "• Công thức:\n"
        "  - ML Quyết định cứng: ŝ = argmin_{s ∈ C} |y - s|²\n"
        "  - Quyết định mềm LLR: LLR(bᵢ|y) = ln(P(bᵢ=0|y) / P(bᵢ=1|y)) ≈ (1/σ²) · [min_{s∈C₁}|y-s|² - min_{s∈C₀}|y-s|²]\n"
        "• Thực tế phần cứng: Quyết định cứng cho hệ thống không mã hóa; LLR mềm cung cấp cho bộ giải mã LDPC để tăng 2-3 dB độ lợi mã hóa.\n"
        "• Chỉ dẫn Debug: Điểm thu càng gần điểm mẫu thì độ lớn |LLR| càng cao (mức tin cậy cao)."
    ),

    # 6. NHÓM RX CODING (Giải mã kênh thu)
    "descramble": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Phép XOR lại với chuỗi giả ngẫu nhiên Gold sequence đồng bộ từ bên phát để khôi phục thứ tự bit ban đầu.\n"
        "• Công thức: b̂ = b̃ ⊕ c.\n"
        "• Thực tế phần cứng: Khôi phục chuỗi bit trước khi đưa vào bộ giải mã kênh.\n"
        "• Chỉ dẫn Debug: Nếu seed hoặc Cell ID bị lệch, chuỗi bit sau giải xáo trộn sẽ có BER ≈ 50%."
    ),
    "rate_recover": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Điền LLR = 0 vào vị trí bit bị chọc lỗ (punctured) và cộng dồn LLR của các gói tin truyền lại HARQ (Chase Combining / IR-HARQ).\n"
        "• Công thức: e → LLR(c); LLR_comb = ∑ LLR_k.\n"
        "• Thực tế phần cứng: Nâng cao SNR hiệu dụng sau mỗi lần truyền lại gói tin lỗi.\n"
        "• Chỉ dẫn Debug: Bit chọc lỗ có LLR = 0 (xác suất 50/50, không có thông tin tiên nghiệm)."
    ),
    "ldpc_decode": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Giải mã lặp lan truyền niềm tin (Belief Propagation - BP) hoặc Min-Sum trên đồ thị Tanner giữa Check Nodes và Variable Nodes.\n"
        "• Công thức: û = LDPCDecode(LLR, I_max); dừng sớm khi thỏa mãn H · ĉᵀ = 0.\n"
        "• Thực tế phần cứng: Chuẩn 5G NR cho phép giải mã song song hàng trăm nút kiểm tra với tốc độ dữ liệu Gbps.\n"
        "• Chỉ dẫn Debug: Đồ thị BER có dạng thác nước (Waterfall), chỉ cách giới hạn Shannon khoảng 0.8 ~ 1.2 dB."
    ),
    "crc_harq": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Tính toán lại mã CRC trên khối dữ liệu đã giải mã; phát tín hiệu ACK nếu không có lỗi hoặc NACK nếu có lỗi.\n"
        "• Công thức: ACK = (CRC(û) == 0).\n"
        "• Thực tế phần cứng: Điều khiển cơ chế truyền lại HARQ ở tầng MAC.\n"
        "• Chỉ dẫn Debug: Tỉ lệ khối lỗi BLER = Tổng số NACK / Tổng số Transport Blocks."
    ),

    # 7. NHÓM METRICS (Đánh giá hiệu năng)
    "sink": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: So sánh từng bit phát và bit thu để tính tỉ lệ lỗi bit thực nghiệm BER = N_errors / N_bits và đối chiếu lý thuyết.\n"
        "• Công thức:\n"
        "  - BER thực nghiệm: BER = (1/N) ∑ I[bᵢ ≠ b̂ᵢ]\n"
        "  - BER lý thuyết BPSK/QPSK: P_b = Q(√(2 Eb/N0)) = 0.5 · erfc(√(Eb/N0))\n"
        "  - BER lý thuyết 16-QAM: P_b ≈ (3/8) · erfc(√(0.4 · Eb/N0))\n"
        "• Thực tế phần cứng: Đo đạc hiệu năng thực tế của tuyến truyền dẫn vô tuyến.\n"
        "• Chỉ dẫn Debug: Ở Eb/N0 = 8 dB (QPSK), BER lý thuyết ≈ 1.9×10⁻⁴; ở 10 dB, BER ≈ 3.8×10⁻⁶."
    ),
    "goodput": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Thông lượng dữ liệu hữu ích thực tế truyền thành công đến người dùng (sau khi trừ hao phí overhead và gói tin lỗi NACK).\n"
        "• Công thức: Goodput = R_raw · (1 - BLER) · (1 - Overhead).\n"
        "• Thực tế phần cứng: Thể hiện trải nghiệm tốc độ mạng thực tế của người dùng cuối (User Throughput).\n"
        "• Chỉ dẫn Debug: Khi SNR tăng, BLER → 0 và Goodput tiệm cận tốc độ truyền cực đại của bậc điều chế."
    ),
    "runtime": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Đo thời gian thực thi chuỗi xử lý tín hiệu phát và thu (Baseband latency).\n"
        "• Công thức: T_total = T_TX + T_channel + T_RX.\n"
        "• Thực tế phần cứng: Đánh giá độ trễ phục vụ các dịch vụ 5G siêu tin cậy và độ trễ thấp (URLLC < 1 ms).\n"
        "• Chỉ dẫn Debug: Số vòng lặp giải mã LDPC càng lớn thì độ trễ xử lý càng tăng."
    ),
    "policy_log": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Ghi lại toàn bộ lịch sử các quyết định thích ứng (trạng thái kênh s_t, hành động chọn MCS a_t, phần thưởng r_t).\n"
        "• Công thức: Trace log = {(s_t, a_t, r_t)} qua từng khung thời gian TTI.\n"
        "• Thực tế phần cứng: Dùng để phân tích tính ổn định của giải thuật thích ứng đường truyền Link Adaptation.\n"
        "• Chỉ dẫn Debug: Kiểm tra xem thuật toán có bị dao động (ping-pong MCS switching) khi kênh dao động nhẹ hay không."
    ),

    # 8. NHÓM ADAPTATION (Vòng lặp thích nghi phản hồi)
    "channel_state": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Đánh giá toàn diện trạng thái kênh vô tuyến dựa trên SINR tức thời, phương sai sai số kênh σ_CSI² và độ dịch Doppler f_D.\n"
        "• Công thức: s_t = [SINR, σ_CSI², f_D, τ_rms].\n"
        "• Thực tế phần cứng: Cung cấp đầu vào trạng thái cho thuật toán chọn tốc độ AMC ở trạm phát (gNodeB).\n"
        "• Chỉ dẫn Debug: SINR cao → Kênh chất lượng tốt; Doppler cao → Kênh biến đổi nhanh theo thời gian."
    ),
    "feedback": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Thu thập báo cáo phản hồi từ máy thu: chỉ số chất lượng kênh CQI (1~15), chỉ số ma trận tiền mã hóa PMI, chỉ số rank RI và chuỗi ACK/NACK (3GPP TS 38.214).\n"
        "• Công thức: h_t = {CQI, PMI, RI, ACK/NACK}.\n"
        "• Thực tế phần cứng: CQI 1 tương ứng QPSK rate 0.15; CQI 15 tương ứng 256-QAM rate 0.92.\n"
        "• Chỉ dẫn Debug: Phản hồi bị trễ (Feedback delay) có thể làm trạm phát chọn sai MCS nếu người dùng di chuyển nhanh."
    ),
    "policy": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Giải thuật thích nghi đường truyền (Link Adaptation): OLLA (Outer Loop Link Adaptation) hoặc Học tăng cường (Reinforcement Learning).\n"
        "• Công thức: a_t = π(s_t, h_t); điều chỉnh ngưỡng SINR để duy trì mục tiêu BLER = 10%.\n"
        "• Thực tế phần cứng: Khi nhận NACK → giảm bậc MCS; khi nhận ACK liên tiếp → nâng bậc MCS để tăng thông lượng.\n"
        "• Chỉ dẫn Debug: Giữ tỉ lệ lỗi khối BLER mục tiêu ổn định quanh mức 10% theo chuẩn 3GPP."
    ),
    "mcs_select": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Lựa chọn cặp thông số Điều chế và Tốc độ mã hóa (Modulation and Coding Scheme - MCS) tối ưu từ bảng chuẩn 3GPP TS 38.214.\n"
        "• Công thức: a_MCS = (M, R_c).\n"
        "• Thực tế phần cứng: Tự động chuyển đổi mượt mà giữa QPSK, 16-QAM, 64-QAM, 256-QAM tùy theo chất lượng sóng.\n"
        "• Chỉ dẫn Debug: Kênh tốt chuyển sang 16-QAM/64-QAM; kênh xấu chuyển sang QPSK/BPSK để bảo toàn dữ liệu."
    ),
    "complexity_select": (
        "[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n"
        "• Nguyên lý: Điều khiển thích ứng độ phức tạp xử lý của máy thu: số vòng lặp giải mã LDPC (I_dec) và giải thuật cân bằng kênh (ZF vs LMMSE).\n"
        "• Công thức: a_C = (I_dec, T_budget).\n"
        "• Thực tế phần cứng: Tiết kiệm năng lượng pin cho thiết bị đầu cuối di động (UE) khi ở vùng sóng tốt.\n"
        "• Chỉ dẫn Debug: Ở SNR cao chỉ cần 3-5 vòng lặp LDPC; ở SNR thấp tăng lên 15-25 vòng lặp."
    ),
}
