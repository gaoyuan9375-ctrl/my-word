import streamlit as st
import time
import json
import os
import datetime

# 设置网页标题、图标和宽屏布局
st.set_page_config(page_title="家庭智能仓储系统 15.0", page_icon="📦", layout="wide")

# ================= 💾 JSON 本地数据读取与保存函数 =================
MENU_FILE = "database_menu_v15.json"
ORDER_FILE = "database_orders_v15.json"
HISTORY_FILE = "database_history_v15.json"   
STOCK_FILE = "database_stock_v15.json"       

def load_data(file_name, default_value):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_value

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= 初始化数据 =================
if "menu" not in st.session_state:
    default_menu = {
        "番茄炒蛋": {"method": "做法：鸡蛋打散炒熟捞出。锅留底油下番茄炒出沙，倒回鸡蛋，加盐、少许糖翻炒。", "keywords": ["番茄", "鸡蛋"]},
        "红烧肉": {"method": "做法：五花肉切块边炒上色，加生抽、老抽、八角和水，小火焖40分钟收汁。", "keywords": ["五花肉", "肉"]},
        "清炒时蔬": {"method": "做法：热油下蒜片爆香，放入蔬菜大火快炒，加盐调味即可出锅。", "keywords": ["蔬菜", "青菜", "白菜"]}
    }
    st.session_state.menu = load_data(MENU_FILE, default_menu)
    save_data(MENU_FILE, st.session_state.menu)

st.session_state.orders = load_data(ORDER_FILE, [])
st.session_state.history = load_data(HISTORY_FILE, {"orders": []})
st.session_state.stock = load_data(STOCK_FILE, [])

# ================= 🧮 核心算法：仅计算库存缺口，不熔断 =================
def check_stock_status(dish_name, qty):
    """仅用于提示库存状态，不限制点餐"""
    if dish_name not in st.session_state.menu:
        return True, ""
    
    kws = st.session_state.menu[dish_name].get("keywords", [])
    stock_items = [s["item"] for s in st.session_state.stock]
    
    missing = []
    for kw in kws:
        count = sum(1 for item in stock_items if kw in item or item in kw)
        if count < qty:
            missing.append(kw)
            
    if missing:
        return False, f"⚠️ 冰箱暂缺核心食材: {', '.join(missing)} (大厨可能需要采购)"
    return True, "🟩 冰箱食材充足"

# ================= 网页大标题 =================
st.title("📦 家庭智能仓储系统 15.0")
st.markdown("🎯 **开放与微调：** 取消了强力熔断锁死，新增【食材保存天数自动计算】功能，让资产一目了然！")
st.divider()

# ================= 网页主体 =================
col_left, col_middle, col_right = st.columns([1.2, 0.9, 0.9])

# --- 【左轴】：自由开放点餐区 ---
with col_left:
    st.markdown("### 🛒 自由点餐区")
    
    name = st.text_input("👤 享用人姓名：", placeholder="谁要吃这道菜...", key="user_name")
    
    menu_list = list(st.session_state.menu.keys())
    dish_selected = st.selectbox("🍲 选择核心菜品：", menu_list if menu_list else ["暂无菜品"])
    
    quantity = st.number_input("🔢 点餐数量(份)：", min_value=1, max_value=10, value=1, step=1)
    
    st.markdown("🛠️ **个性化加工偏好：**")
    taste_pref = st.multiselect("🌶️ 口味偏好：", ["少盐", "少油", "不加葱蒜", "重辣"])
    custom_add = st.text_input("➕ 自由加料：", placeholder="如：加土豆")

    # 检查库存并显示提示，但【不锁死按钮】
    is_enough, tip_msg = check_stock_status(dish_selected, quantity)
    if not is_enough:
        st.warning(tip_msg)
    else:
        st.caption(tip_msg)

    # 按钮保持永远可用状态
    if st.button("🔥 发送点餐指令", type="primary", use_container_width=True):
        if name.strip() == "": 
            st.error("请署名后再发送点餐指令！")
        else:
            current_time = time.strftime("%H:%M", time.localtime())
            notes = list(taste_pref)
            if custom_add.strip(): notes.append(custom_add.strip())
            note_str = "，".join(notes) if notes else "标准工艺烹饪"
            
            st.session_state.orders.append({
                "time": current_time, "name": name, "dish": dish_selected,
                "qty": int(quantity), "note": note_str, "date": time.strftime("%Y-%m-%d")
            })
            save_data(ORDER_FILE, st.session_state.orders)
            st.success(f"🎉 点餐成功！{name} 的 {quantity} 份【{dish_selected}】已加入排单！")
            time.sleep(0.5)
            st.rerun()

# --- 【中轴】：核心菜谱库与智能食材缺口分析 ---
with col_middle:
    st.markdown("### 📖 核心菜谱库与做法")
    if menu_list:
        dish_to_look = st.selectbox("调取配方与做法：", menu_list, key="look_up")
        st.info(st.session_state.menu[dish_to_look]["method"])
        
        kws = st.session_state.menu[dish_to_look].get("keywords", [])
        stock_items = [s["item"] for s in st.session_state.stock]
        
        st.markdown("**🔍 冰箱库存匹配状态：**")
        for kw in kws:
            has_kw = any(kw in item or item in kw for item in stock_items)
            if has_kw: st.success(f"🟩 冰箱已有：**{kw}**")
            else: st.error(f"🟥 冰箱缺失：**{kw}**")

# --- 【右轴】：菜篮子数字仓储入库 ---
with col_right:
    st.markdown("### 🥬 菜篮子仓储数字入库")
    exp_item = st.text_input("🛒 买入食材名称：", placeholder="例如：五花肉 / 鸡蛋")
    buy_date = st.date_input("📅 请选择买菜日期：", datetime.date.today())
    
    if st.button("✅ 食材实体存入冰箱", type="primary", use_container_width=True):
        if exp_item.strip() == "": st.error("请输入食材名称！")
        else:
            st.session_state.stock.append({"item": exp_item, "buy_date": str(buy_date)})
            save_data(STOCK_FILE, st.session_state.stock)
            st.success(f"📦 成功入库：{exp_item} (登记日期: {buy_date})")
            time.sleep(0.5)
            st.rerun()
            
    st.markdown("---")
    st.markdown("### ⚙️ 扩充膳食菜单库")
    new_dish_name = st.text_input("✨ 新增菜名：")
    new_dish_kws = st.text_input("🏷️ 食材标签(逗号隔开)：")
    new_dish_method = st.text_area("📝 做法步骤：")
    if st.button("💾 归档至膳食系统", use_container_width=True):
        if new_dish_name.strip() and new_dish_method.strip():
            kw_list = [k.strip() for k in new_dish_kws.replace("，", ",").split(",") if k.strip()]
            st.session_state.menu[new_dish_name] = {"method": "做法：" + new_dish_method, "keywords": kw_list}
            save_data(MENU_FILE, st.session_state.menu)
            st.success(f"✅ 《{new_dish_name}》已录入！")
            time.sleep(0.5)
            st.rerun()

# ================= 4. 下半部分：今日大厨智能聚合合单看板 =================
st.divider()
st.markdown("### 📋 今日大厨智能聚合合单看板")

if not st.session_state.orders: 
    st.caption("目前暂无有效加工指令。")
else:
    summary_dict = {}
    for order in st.session_state.orders:
        dish = order["dish"]
        qty = order["qty"]
        detail_str = f"👤 {order['name']} ({qty}份) 💡 要求: {order['note']}"
        if dish not in summary_dict: summary_dict[dish] = {"total_qty": 0, "details": []}
        summary_dict[dish]["total_qty"] += qty
        summary_dict[dish]["details"].append(detail_str)
    
    for dish_name, info in summary_dict.items():
        st.markdown(f"#### 🍲 **{dish_name}** ×  == `{info['total_qty']} 份` ==")
        for det in info["details"]: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; • {det}")
        st.divider()
    
    if st.button("🍳 今日做饭完毕（一键出库并归档）", type="primary", use_container_width=True):
        required_keywords = []
        for order in st.session_state.orders:
            dish_name = order["dish"]
            qty = order["qty"]
            if dish_name in st.session_state.menu:
                kws = st.session_state.menu[dish_name].get("keywords", [])
                for _ in range(qty): required_keywords.extend(kws)
        
        updated_stock = []
        for stock_node in st.session_state.stock:
            item_name = stock_node["item"]
            matched_kw = None
            for kw in required_keywords:
                if kw in item_name or item_name in kw:
                    matched_kw = kw
                    break
            if matched_kw:
                required_keywords.remove(matched_kw)
                continue
            else:
                updated_stock.append(stock_node)
        
        st.session_state.stock = updated_stock
        save_data(STOCK_FILE, st.session_state.stock)
        
        st.session_state.history["orders"].extend(st.session_state.orders)
        save_data(HISTORY_FILE, st.session_state.history)
        st.session_state.orders = []
        save_data(ORDER_FILE, [])
        st.success("🎉 生产指令执行完毕，实体库存已根据实际消耗完成扣减！")
        time.sleep(1.0)
        st.rerun()

# ================= 5. 最下方：智能仓储明细大屏（带保存天数计算） =================
st.divider()
st.header("⏳ 📊 智能仓储明细大屏")
tab1, tab2 = st.tabs(["🚦 冰箱实体库存清单", "📂 时光机历史档案"])

with tab1:
    if not st.session_state.stock: 
        st.caption("冰箱目前处于清空状态。")
    else:
        st.markdown("**👇 当前冰箱小仓库明细（自动计算已保存天数）：**")
        today = datetime.date.today()
        
        for idx, s in enumerate(st.session_state.stock):
            # 🌟 核心升级：解析保存的购买日期，并计算已经保存了几天
            try:
                b_date = datetime.datetime.strptime(s['buy_date'], "%Y-%m-%d").date()
                days_saved = (today - b_date).days
                if days_saved < 0: days_saved = 0 # 容错
                days_str = f" 🔥 已保存 `{days_saved}` 天"
            except:
                days_str = " ⚠️ 未知登记时间"
                
            st.info(f"📦 物品 #{idx+1}： **{s['item']}** | 📥 入库登记日期： `{s['buy_date']}` | {days_str}")
            
        if st.button("🧹 一键强制清空冰箱"):
            st.session_state.stock = []
            save_data(STOCK_FILE, [])
            st.rerun()

with tab2:
    if st.session_state.history["orders"]:
        for h_order in st.session_state.history["orders"]:
            st.markdown(f"⏱️ `{h_order.get('date', '历史')}` | 👤 **{h_order['name']}** 曾享用了 `{h_order.get('qty', 1)}份` 🍲 **{h_order['dish']}**")