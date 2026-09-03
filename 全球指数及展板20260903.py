import os
import json
import time
import random
import pandas as pd
import yfinance as yf
import baostock as bs
from requests import Session

# ==================== 第一部分：数据自动获取与同步模块 ====================

session = Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
})

# 1. 扩充后的全球核心指数与科创板配置（带地理位置经纬度用于 ECharts 地图渲染）
indices_config = {
    # --- 中国大陆市场 (使用 BaoStock) ---
    "上证指数": {"ticker": "sh.000001", "en": "Shanghai Comp", "lon": 102, "lat": 35, "filename": "上证指数_000001.SS_history.csv", "source": "bs", "start": "1990-12-19"},
    "深证成指": {"ticker": "sz.399001", "en": "Shenzhen Comp", "lon": 110, "lat": 24, "filename": "深证成指_399001.SZ_history.csv", "source": "bs", "start": "1991-04-03"},
    "创业板指": {"ticker": "sz.399006", "en": "ChiNext", "lon": 118, "lat": 35, "filename": "创业板指_399006.SZ_history.csv", "source": "bs", "start": "2010-06-01"},
    "沪深300": {"ticker": "sh.000300", "en": "CSI 300", "lon": 110, "lat": 41, "filename": "沪深300_000300.SS_history.csv", "source": "bs", "start": "2005-04-08"},
    "科创50": {"ticker": "sh.000688", "en": "STAR 50", "lon": 105, "lat": 28, "filename": "科创50_000688.SS_history.csv", "source": "bs", "start": "2020-07-23"},
    "科创100": {"ticker": "sh.000698", "en": "STAR 100", "lon": 115, "lat": 29, "filename": "科创100_000698.SS_history.csv", "source": "bs", "start": "2023-08-07"},

    # --- 港台地区与亚太及大洋洲市场 ---
    "香港恒生指数": {"ticker": "^HSI", "en": "Hang Seng", "lon": 115, "lat": 16, "filename": "香港恒生指数_HSI_history.csv", "source": "yf"},
    "台湾加权指数": {"ticker": "^TWII", "en": "TAIEX", "lon": 126, "lat": 23, "filename": "台湾加权指数_TWII_history.csv", "source": "yf"},
    "日经225": {"ticker": "^N225", "en": "Nikkei 225", "lon": 142, "lat": 38, "filename": "日经225_N225_history.csv", "source": "yf"},
    "韩国综合指数": {"ticker": "^KS11", "en": "KOSPI", "lon": 132, "lat": 30, "filename": "韩国综合指数_KS11_history.csv", "source": "yf"},
    "澳大利亚普通股": {"ticker": "^AORD", "en": "All Ordinaries", "lon": 138, "lat": -26, "filename": "澳大利亚普通股指数_AORD_history.csv", "source": "yf"},
    "新西兰NZ50": {"ticker": "^NZ50", "en": "NZX 50", "lon": 170, "lat": -40, "filename": "新西兰NZ50指数_NZ50_history.csv", "source": "yf"},

    # --- 美洲市场 ---
    "道琼斯": {"ticker": "^DJI", "en": "Dow Jones", "lon": -112, "lat": 46, "filename": "道琼斯_DJI_history.csv", "source": "yf"},
    "标普500": {"ticker": "^GSPC", "en": "S&P 500", "lon": -98, "lat": 32, "filename": "标普500_GSPC_history.csv", "source": "yf"},
    "纳斯达克": {"ticker": "^IXIC", "en": "NASDAQ", "lon": -85, "lat": 42, "filename": "纳斯达克_IXIC_history.csv", "source": "yf"},
    "多伦多综合": {"ticker": "^GSPTSE", "en": "S&P/TSX", "lon": -105, "lat": 58, "filename": "多伦多股票交易所综合_GSPTSE_history.csv", "source": "yf"},
    "圣保罗IBOV": {"ticker": "^BVSP", "en": "Ibovespa", "lon": -52, "lat": -18, "filename": "圣保罗IBOVESPA指数_BVSP_history.csv", "source": "yf"},
    "墨西哥MXX": {"ticker": "^MXX", "en": "IPC Mexico", "lon": -100, "lat": 20, "filename": "墨西哥MXX指数_MXX_history.csv", "source": "yf"},

    # --- 欧洲市场 ---
    "英国富时100": {"ticker": "^FTSE", "en": "FTSE 100", "lon": -18, "lat": 56, "filename": "英国富时100_FTSE_history.csv", "source": "yf"},
    "德国DAX": {"ticker": "^GDAXI", "en": "DAX", "lon": 8, "lat": 52, "filename": "德国DAX_GDAXI_history.csv", "source": "yf"},
    "法国CAC40": {"ticker": "^FCHI", "en": "CAC 40", "lon": -2, "lat": 45, "filename": "法国CAC40_FCHI_history.csv", "source": "yf"},
    "意大利MIB": {"ticker": "FTSEMIB.MI", "en": "FTSE MIB", "lon": 16, "lat": 43, "filename": "意大利MIB_FTSEMIB_history.csv", "source": "yf"},
    "西班牙IBEX35": {"ticker": "^IBEX", "en": "IBEX 35", "lon": -6, "lat": 38, "filename": "西班牙IBEX35_IBEX_history.csv", "source": "yf"},
    "瑞士苏黎世": {"ticker": "^SSMI", "en": "SMI Zurich", "lon": 10, "lat": 46, "filename": "瑞士苏黎世市场指数_SSMI_history.csv", "source": "yf"},
    "俄罗斯MOEX": {"ticker": "IMOEX.ME", "en": "MOEX Russia", "lon": 37, "lat": 55, "filename": "俄罗斯RTS指数_IMOEX_history.csv", "source": "yf"},
}

# 2. 美国核心 ETF 资产配置（严格规范在非洲大陆内部的 3x3 矩阵区域内，整齐美观不重叠）
etfs_config = {
    "QQQ": {"ticker": "QQQ", "en": "Invesco QQQ Trust", "lon": 15, "lat": 22, "filename": "QQQ_ETF_history.csv", "source": "yf"},
    "QQQM": {"ticker": "QQQM", "en": "Nasdaq 100 ETF", "lon": 25, "lat": 22, "filename": "QQQM_ETF_history.csv", "source": "yf"},
    "VOO": {"ticker": "VOO", "en": "Vanguard S&P 500 ETF", "lon": 35, "lat": 22, "filename": "VOO_ETF_history.csv", "source": "yf"},
    "SPY": {"ticker": "SPY", "en": "SPDR S&P 500 ETF", "lon": 15, "lat": 2, "filename": "SPY_ETF_history.csv", "source": "yf"},
    "DGRO": {"ticker": "DGRO", "en": "Core Dividend Growth", "lon": 25, "lat": 2, "filename": "DGRO_ETF_history.csv", "source": "yf"},
    "SCHD": {"ticker": "SCHD", "en": "Schwab U.S. Dividend", "lon": 35, "lat": 2, "filename": "SCHD_ETF_history.csv", "source": "yf"},
    "VYM": {"ticker": "VYM", "en": "Vanguard High Dividend", "lon": 15, "lat": -16, "filename": "VYM_ETF_history.csv", "source": "yf"},
    "SMH": {"ticker": "SMH", "en": "VanEck Semiconductor", "lon": 25, "lat": -16, "filename": "SMH_ETF_history.csv", "source": "yf"},
    "TQQQ": {"ticker": "TQQQ", "en": "ProShares UltraPro QQQ", "lon": 35, "lat": -16, "filename": "TQQQ_ETF_history.csv", "source": "yf"},
}

all_configs = {**indices_config, **etfs_config}

data_dir = "market_history_data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

print("开始同步全球指数、科创板及扩展版核心 ETF 历史数据...\n")
today_str = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

for name, info in all_configs.items():
    ticker = info["ticker"]
    file_path = os.path.join(data_dir, info["filename"])
    source = info["source"]

    if os.path.exists(file_path) and os.path.getsize(file_path) < 2048:
        os.remove(file_path)

    if source == "yf":
        for attempt in range(3):
            try:
                if os.path.exists(file_path):
                    df_local = pd.read_csv(file_path, parse_dates=["Date"])
                    df_local["Date"] = pd.to_datetime(df_local["Date"]).dt.tz_localize(None)
                    df_local = df_local.sort_values("Date").reset_index(drop=True)

                    last_date = df_local["Date"].max()
                    start_date = (last_date - pd.Timedelta(days=5)).strftime("%Y-%m-%d")

                    df_new = yf.download(ticker, start=start_date, end=today_str, progress=False, session=session)
                    if not df_new.empty:
                        if isinstance(df_new.columns, pd.MultiIndex):
                            df_new.columns = df_new.columns.get_level_values(0)
                        df_new = df_new.reset_index()
                        df_new["Date"] = pd.to_datetime(df_new["Date"]).dt.tz_localize(None)

                        df_combined = pd.concat([df_local, df_new]).drop_duplicates(subset=["Date"])
                        df_combined = df_combined.sort_values("Date").reset_index(drop=True)
                        df_combined.to_csv(file_path, index=False)
                else:
                    df_all = yf.download(ticker, period="max", progress=False, session=session)
                    if not df_all.empty:
                        if isinstance(df_all.columns, pd.MultiIndex):
                            df_all.columns = df_all.columns.get_level_values(0)
                        df_all = df_all.reset_index()
                        df_all["Date"] = pd.to_datetime(df_all["Date"]).dt.tz_localize(None)
                        df_all = df_all.sort_values("Date").reset_index(drop=True)
                        df_all.to_csv(file_path, index=False)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep((attempt + 1) * 5)
                else:
                    print(f"[{name}] yfinance 获取失败: {e}")
        time.sleep(random.uniform(1.0, 2.0))

    elif source == "bs":
        lg = bs.login()
        if lg.error_code == '0':
            query_start_date = info.get("start", "1990-12-19")
            if os.path.exists(file_path):
                try:
                    df_local = pd.read_csv(file_path, parse_dates=["Date"])
                    last_date_str = df_local["Date"].max().strftime("%Y-%m-%d")
                    query_start_date = (pd.Timestamp(last_date_str) - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
                except:
                    pass

            rs = bs.query_history_k_data_plus(
                ticker, "date,open,high,low,close,volume",
                start_date=query_start_date, end_date=today_str,
                frequency="d", adjustflag="3"
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if data_list:
                df_bs = pd.DataFrame(data_list, columns=rs.fields)
                for col in ["open", "high", "low", "close", "volume"]:
                    df_bs[col] = pd.to_numeric(df_bs[col], errors="coerce")

                df_bs = df_bs.rename(
                    columns={"date": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close",
                             "volume": "Volume"})
                df_bs["Adj Close"] = df_bs["Close"]

                if os.path.exists(file_path):
                    df_local = pd.read_csv(file_path)
                    df_combined = pd.concat([df_local, df_bs]).drop_duplicates(subset=["Date"])
                    df_combined = df_combined.sort_values("Date").reset_index(drop=True)
                    df_combined.to_csv(file_path, index=False)
                else:
                    columns_order = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
                    df_bs = df_bs[[col for col in columns_order if col in df_bs.columns]]
                    df_bs = df_bs.sort_values("Date").reset_index(drop=True)
                    df_bs.to_csv(file_path, index=False)

            bs.logout()

print("所有历史数据同步完成！正在生成看板...\n")

# ==================== 第二部分：前端 HTML 生成模块 ====================

all_stocks_data = {}
for name, info in all_configs.items():
    file_path = os.path.join(data_dir, info["filename"])
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, parse_dates=["Date"])
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
            df = df.sort_values("Date")
            df = df.dropna(subset=["Date", "Close"])

            records = [{"date": row["Date"].strftime("%Y-%m-%d"), "close": float(row["Close"])} for _, row in df.iterrows()]
            all_stocks_data[name] = {
                "en": info["en"],
                "lon": info.get("lon", 0),
                "lat": info.get("lat", 0),
                "records": records
            }
        except Exception as e:
            print(f"解析 {name} 本地数据出错: {e}")

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>全球主要指数与核心 ETF 区间表现看板</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/js/world.js"></script>
    <style>
        body {
            background-color: #161616;
            margin: 0;
            padding: 0;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        #toolbar {
            position: absolute;
            top: 15px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 999;
            background: rgba(30, 30, 30, 0.95);
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid #444;
            display: flex;
            gap: 5px;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6);
            flex-wrap: wrap;
            justify-content: center;
        }
        #toolbar label, #toolbar span {
            font-size: 12px;
            color: #ccc;
        }
        #toolbar input, #toolbar button {
            background: #2a2a2a;
            color: #fff;
            border: 1px solid #555;
            padding: 4px 6px;
            border-radius: 4px;
            font-size: 12px;
            outline: none;
        }
        #toolbar button {
            background: #333;
            cursor: pointer;
            font-weight: 500;
        }
        #toolbar button:hover {
            background: #444;
        }
        .action-btn {
            background: #007acc !important;
            border-color: #0062a3 !important;
            font-weight: bold !important;
        }
        .action-btn:hover {
            background: #0098ff !important;
        }

        .dropdown {
            position: relative;
            display: inline-block;
        }
        .dropdown-btn {
            background: #2a2a2a;
            color: #fff;
            border: 1px solid #555;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
        }
        .dropdown-content {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            background: #222;
            min-width: 180px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #444;
            border-radius: 4px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.7);
            z-index: 1000;
            padding: 6px;
        }
        .dropdown-content.show {
            display: block;
        }
        .dropdown-content label {
            display: block;
            padding: 4px 6px;
            font-size: 11px;
            cursor: pointer;
            color: #ddd;
            white-space: nowrap;
        }
        .dropdown-content label:hover {
            background: #333;
        }
        .dropdown-actions {
            display: flex;
            justify-content: space-between;
            padding: 4px 4px 6px 4px;
            border-bottom: 1px solid #444;
            margin-bottom: 4px;
        }
        .dropdown-actions button {
            font-size: 10px;
            padding: 2px 6px;
        }

        #main {
            width: 100vw;
            height: 100vh;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <div class="dropdown">
            <button class="dropdown-btn" onclick="toggleDropdown()">📊 标的筛选 ▾</button>
            <div id="dropdownList" class="dropdown-content">
                <div class="dropdown-actions">
                    <button onclick="selectAll(true)">全选</button>
                    <button onclick="selectAll(false)">清空</button>
                </div>
            </div>
        </div>
        <span style="border-left: 1px solid #555; height: 16px; margin: 0 2px;"></span>
        <button onclick="setPreset('prev1d')">前1天</button>
        <button onclick="setPreset('1d')">1天</button>
        <button onclick="setPreset('5d')">5天</button>
        <button onclick="setPreset('1m')">1个月</button>
        <button onclick="setPreset('3m')">3个月</button>
        <button onclick="setPreset('ytd')">YTD</button>
        <button onclick="setPreset('1y')">1年</button>
        <button onclick="setPreset('3y')">3年</button>
        <button onclick="setPreset('5y')">5年</button>
        <button onclick="setPreset('10y')">10年</button>
        <button onclick="setPreset('20y')">20年</button>
        <button onclick="setPreset('50y')">50年</button>
        <button onclick="setPreset('max')">MAX</button>
        <span style="border-left: 1px solid #555; height: 16px; margin: 0 2px;"></span>
        <label>开始:</label>
        <input type="date" id="startDate" value="2024-01-01">
        <label>结束:</label>
        <input type="date" id="endDate" value="">
        <button class="action-btn" onclick="updateChart()">立即更新</button>
    </div>

    <div id="main"></div>

    <script>
        var stockDatabase = REPLACE_STOCK_DATA_PLACEHOLDER;

        var dropdownList = document.getElementById('dropdownList');
        for (var name in stockDatabase) {
            var lbl = document.createElement('label');
            lbl.innerHTML = '<input type="checkbox" value="' + name + '" checked onchange="updateChart()"> ' + name + ' (' + stockDatabase[name].en + ')';
            dropdownList.appendChild(lbl);
        }

        function toggleDropdown() {
            document.getElementById('dropdownList').classList.toggle('show');
        }

        window.onclick = function(event) {
            if (!event.target.matches('.dropdown-btn') && !event.target.closest('.dropdown-content')) {
                var dropdowns = document.getElementsByClassName("dropdown-content");
                for (var i = 0; i < dropdowns.length; i++) {
                    var openDropdown = dropdowns[i];
                    if (openDropdown.classList.contains('show')) {
                        openDropdown.classList.remove('show');
                    }
                }
            }
        }

        function selectAll(status) {
            var checkboxes = document.querySelectorAll('#dropdownList input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = status);
            updateChart();
        }

        var globalMaxDate = '2026-08-17';
        for (var k in stockDatabase) {
            var recs = stockDatabase[k].records;
            if (recs && recs.length > 0) {
                var lastDate = recs[recs.length - 1].date;
                if (lastDate > globalMaxDate) globalMaxDate = lastDate;
            }
        }
        document.getElementById('endDate').value = globalMaxDate;

        var chartDom = document.getElementById('main');
        var myChart = echarts.init(chartDom);

        function getProcessedData(startStr, endStr) {
            var results = [];
            var userStartDate = new Date(startStr);
            var userEndDate = new Date(endStr);

            var selectedCheckboxes = document.querySelectorAll('#dropdownList input[type="checkbox"]:checked');
            var selectedNames = Array.from(selectedCheckboxes).map(cb => cb.value);

            for (var name in stockDatabase) {
                if (!selectedNames.includes(name)) continue;

                var item = stockDatabase[name];
                var records = item.records;
                if (!records || records.length === 0) continue;

                var endIndex = -1;
                for (var i = records.length - 1; i >= 0; i--) {
                    if (new Date(records[i].date) <= userEndDate) {
                        endIndex = i;
                        break;
                    }
                }
                if (endIndex === -1) endIndex = records.length - 1;

                var startIndex = -1;
                for (var j = 0; j < records.length; j++) {
                    if (new Date(records[j].date) >= userStartDate) {
                        startIndex = j;
                        break;
                    }
                }
                if (startIndex === -1) startIndex = 0;

                if (startIndex >= endIndex) {
                    startIndex = Math.max(0, endIndex - 1);
                }

                var startRecord = records[startIndex];
                var endRecord = records[endIndex];

                if (startRecord && endRecord && startRecord.date !== endRecord.date) {
                    var startPrice = startRecord.close;
                    var endPrice = endRecord.close;
                    var perf = startPrice > 0 ? ((endPrice - startPrice) / startPrice) * 100 : 0;

                    results.push({
                        name: name,
                        enName: item.en,
                        lon: item.lon,
                        lat: item.lat,
                        perf: parseFloat(perf.toFixed(2)),
                        startDate: startRecord.date,
                        startPrice: startPrice.toFixed(2),
                        endDate: endRecord.date,
                        endPrice: endPrice.toFixed(2)
                    });
                }
            }
            return results;
        }

        function renderMap(startStr, endStr) {
            var processed = getProcessedData(startStr, endStr);

            var scatterData = processed.map(d => ({
                name: d.name,
                enName: d.enName,
                value: [d.lon, d.lat, d.perf],
                startDate: d.startDate,
                startPrice: d.startPrice,
                endDate: d.endDate,
                endPrice: d.endPrice
            }));

            var option = {
                backgroundColor: '#161616',
                title: {
                    text: '全球主要指数与核心 ETF 区间表现看板',
                    subtext: '统计区间: ' + startStr + ' 至 ' + endStr,
                    left: 'center',
                    top: '65px',
                    textStyle: { color: '#ffffff', fontSize: 16 },
                    subtextStyle: { color: '#aaaaaa', fontSize: 12 }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function (params) {
                        var data = params.data;
                        var val = data.value[2];
                        var sign = val > 0 ? '+' : '';
                        return '<b>' + data.name + ' (' + data.enName + ')</b><br/>' +
                               '区间涨跌幅: <span style="color:' + (val > 0 ? '#ff4d4d' : '#2ecc71') + '; font-weight:bold;">' + sign + val.toFixed(2) + '%</span><br/>' +
                               '<hr style="border:0; border-top:1px solid #444; margin:4px 0;">' +
                               '<span style="color:#aaa; font-size:11px;">起始日期 (' + data.startDate + '): <b>' + data.startPrice + '</b></span><br/>' +
                               '<span style="color:#aaa; font-size:11px;">结束日期 (' + data.endDate + '): <b>' + data.endPrice + '</b></span>';
                    }
                },
                geo: {
                    map: 'world',
                    roam: true,
                    zoom: 1.2,
                    center: [20, 20],
                    itemStyle: {
                        areaColor: '#252525',
                        borderColor: '#383838',
                        borderWidth: 0.8
                    },
                    emphasis: {
                        itemStyle: { areaColor: '#303030' }
                    }
                },
                series: [
                    {
                        name: '全球市场表现',
                        type: 'scatter',
                        coordinateSystem: 'geo',
                        data: scatterData,
                        symbolSize: function (val) {
                            return Math.max(Math.min(Math.abs(val[2]) * 2.2 + 65, 140), 65);
                        },
                        label: {
                            show: true,
                            formatter: function (params) {
                                var data = params.data;
                                var val = data.value[2];
                                var sign = val > 0 ? '+' : '';
                                return data.name + '\\n' + sign + val.toFixed(2) + '%';
                            },
                            position: 'inside',
                            color: '#ffffff',
                            fontSize: 11,
                            fontWeight: 'bold',
                            align: 'center',
                            lineHeight: 14
                        },
                        itemStyle: {
                            color: function (params) {
                                return params.value[2] > 0 ? 'rgba(210, 30, 30, 0.75)' : 'rgba(30, 150, 70, 0.75)';
                            },
                            borderColor: function (params) {
                                return params.value[2] > 0 ? '#ff4d4d' : '#2ecc71';
                            },
                            borderWidth: 2.5,
                            shadowBlur: 15,
                            shadowColor: function (params) {
                                return params.value[2] > 0 ? 'rgba(255, 0, 0, 0.5)' : 'rgba(0, 255, 0, 0.5)';
                            }
                        },
                        emphasis: {
                            itemStyle: {
                                borderColor: '#ffffff',
                                borderWidth: 3.5
                            }
                        }
                    }
                ]
            };

            myChart.setOption(option, true);
        }

        function updateChart() {
            var start = document.getElementById('startDate').value;
            var end = document.getElementById('endDate').value;
            if(!start || !end) {
                alert('请选择完整的起止日期！');
                return;
            }
            renderMap(start, end);
        }

        function setPreset(type) {
            var sampleKey = Object.keys(stockDatabase)[0];
            var sampleRecs = stockDatabase[sampleKey].records;
            var lastIdx = sampleRecs.length - 1;

            var targetEndIdx = lastIdx;
            var targetStartIdx = lastIdx;

            if (type === 'prev1d') {
                targetEndIdx = Math.max(0, lastIdx - 1);
                targetStartIdx = Math.max(0, lastIdx - 2);
            } else if (type === '1d') {
                targetEndIdx = lastIdx;
                targetStartIdx = Math.max(0, lastIdx - 1);
            } else if (type === '5d') {
                targetEndIdx = lastIdx;
                targetStartIdx = Math.max(0, lastIdx - 5);
            } else {
                var endObj = new Date(sampleRecs[lastIdx].date);
                var startObj = new Date(endObj);

                if (type === '1m') startObj.setMonth(endObj.getMonth() - 1);
                else if (type === '3m') startObj.setMonth(endObj.getMonth() - 3);
                else if (type === 'ytd') startObj = new Date(endObj.getFullYear(), 0, 1);
                else if (type === '1y') startObj.setFullYear(endObj.getFullYear() - 1);
                else if (type === '3y') startObj.setFullYear(endObj.getFullYear() - 3);
                else if (type === '5y') startObj.setFullYear(endObj.getFullYear() - 5);
                else if (type === '10y') startObj.setFullYear(endObj.getFullYear() - 10);
                else if (type === '20y') startObj.setFullYear(endObj.getFullYear() - 20);
                else if (type === '50y') startObj.setFullYear(endObj.getFullYear() - 50);
                else if (type === 'max') startObj = new Date('1900-01-01');

                document.getElementById('startDate').value = startObj.toISOString().split('T')[0];
                document.getElementById('endDate').value = sampleRecs[lastIdx].date;
                updateChart();
                return;
            }

            document.getElementById('startDate').value = sampleRecs[targetStartIdx].date;
            document.getElementById('endDate').value = sampleRecs[targetEndIdx].date;
            updateChart();
        }

        setPreset('ytd');

        window.addEventListener('resize', function () {
            myChart.resize();
        });
    </script>
</body>
</html>
"""

json_data_str = json.dumps(all_stocks_data, ensure_ascii=False)
html_content = html_content.replace("REPLACE_STOCK_DATA_PLACEHOLDER", json_data_str)

output_file = "global_market_bubble_map.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"全量指数（含科创50、科创100等）与9只核心ETF已成功同步，看板已更新至 {output_file}！")

这个代码实现了什么功能