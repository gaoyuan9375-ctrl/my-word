import streamlit as st
import time
import json
import os
import datetime

# 设置网页标题、图标和宽屏布局
st.set_page_config(page_title="家庭智能仓储系统 16.0", page_icon="📦", layout="wide")

# ================= 💾 JSON 本地数据读取与保存函数 =================
MENU_FILE = "database_menu_v16.json"
ORDER_FILE = "database_orders_v16.json"
HISTORY_FILE = "database_history_v16.json"   
STOCK_FILE = "database_stock_v16.json"       
USERS_FILE = "database_users_v16.json"       # 新增：家庭成员花名册数据库

def load_data(file_name, default_value):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_value

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= 初始化基础数据 =================
if "menu" not in st.session_state:
    default_menu = {
        "番茄炒蛋": {"method": "做法：鸡蛋打散炒熟捞出。锅留底油下番茄炒出沙，倒回鸡蛋，加盐、少许糖翻炒。", "keywords": ["番茄", "鸡蛋"]},
        "红烧肉": {"method": "做法：五花肉切块边炒上色，加生抽、老抽、八角和水，小火焖40分钟收汁。", "keywords": ["五花肉", "肉"]},
        "清炒时蔬": {"method": "做法：热油下蒜片爆香，放入蔬菜大火快炒，加盐调味即可出锅。", "keywords": ["蔬菜", "青菜", "白菜"]}
    }
    st.session_state.menu = load_data(MENU_FILE, default_menu)

# 初始化家庭成员花名册
if "users" not in st.session_state:
    default_users = ["老爸", "老妈", "宝贝"]
    st.session_state.users = load_data(USERS_FILE, default_users)

st.session_state.orders = load_data(ORDER_FILE, [])
st.session_state.history = load_data(HISTORY_FILE, {"orders": []})
st.session_state.stock = load_data(STOCK_FILE, [])

# ================= 🧮 供应链辅助算法 =================
def check_stock_status(dish_name, qty):
    """仅用于提示库存状态和汇总缺口"""
    if dish_name not in st.session_state.menu:
        return True, []
    kws = st.session_state.menu[dish_name].get("keywords", [])
    stock_items = [s["item"] for s in st.session_state.stock]
    missing = []
    for kw in kws:
        count = sum(1 for item in stock_items if kw in item or item in kw)
        if count < qty:
            missing.append(kw)
    return len(missing) == 0, missing

# ================= 网页大标题 =================
st.title("📦 家庭智能仓储系统 16.0")
st.markdown("🎯 **主厨效率倍增：** 享用人升级为【下拉选择+动态花名册管理】，引入【保存天数分级标签】与【一键复制微信采购清单】！")
st.divider()

# ================= 网页主体布局 =================
col_left, col_middle, col_right = st.columns([1.2, 0.9, 0.9])

# --- 【左轴】：选单与享用人管理区 ---
with col_left:
    st.markdown("### 🛒 享用人点餐区")
    
    # 🌟 核心升级：享用人改为下拉框选择
    if not st.session_state.users:
        st.error("⚠️ 花名册为空，请先在下方添加家庭成员！")
        current_user = None
    else:
        current_user = st.selectbox("👤 请选择你的名字：", st.session_state.users)
    
    quantity = st.number_input("🔢 点餐数量(份)：", min_value=1, max_value=10, value=1, step=1)
    
    menu_list = list(st.session_state.menu.keys())
    dish_selected = st.selectbox("🍲 选择核心菜品：", menu_list if menu_list else ["暂无菜品"])
    
    st.markdown("🛠️ **个性化加工偏好：**")
    taste_pref = st.multiselect("🌶️ 口味偏好：", ["少盐", "少油", "不加葱蒜", "重辣"])
    custom_add = st.text_input("➕ 自由加料：", placeholder="如：加土豆")

    # 检查库存缺口提示
    is_enough, missing_kws = check_stock_status(dish_selected, quantity)
    if not is_enough:
        st.warning(f"⚠️ 冰箱暂缺核心食材: {', '.join(missing_kws)} (仍可强行点餐)")
    else:
        st.caption("🟩 冰箱食材充足")

    if st.button("🔥 发送点餐指令", type="primary", use_container_width=True):
        if not current_user:
            st.error("无法提交：未选中有效的享用人！")
        else:
            current_time = time.strftime("%H:%M", time.localtime())
            notes = list(taste_pref)
            if custom_add.strip(): notes.append(custom_add.strip())
            note_str = "，".join(notes) if notes else "标准工艺烹饪"
            
            st.session_state.orders.append({
                "time": current_time, "name": current_user, "dish": dish_selected,
                "qty": int(quantity), "note": note_str, "date": time.strftime("%Y-%m-%d")
            })
            save_data(ORDER_FILE, st.session_state.orders)
            st.success(f"🎉 点餐成功！{current_user} 的 {quantity} 份【{dish_selected}】已排单！")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    # 🌟 核心升级：动态添加和编辑享用人花名册
    with st.expander("👥 ⚙️ 家庭成员花名册增删管理"):
        st.markdown("**🎨 当前花名册：** " + " | ".join([f"`{u}`" for u in st.session_state.users]))
        
        new_user = st.text_input("➕ 添加新成员名字：", placeholder="例如：奶奶、外婆")
        if st.button("💾 确认添加新成员", use_container_width=True):
            if new_user.strip() == "": st.error("名字不能为空！")
            elif new_user.strip() in st.session_state.users: st.warning("此成员已在花名册中！")
            else:
                st.session_state.users.append(new_user.strip())
                save_data(USERS_FILE, st.session_state.users)
                st.success(f"✅ 已成功将【{new_user}】录入家庭花名册！")
                time.sleep(0.5)
                st.rerun()
                
        user_to_del = st.selectbox("❌ 选择要移出的成员：", ["请选择..."] + st.session_state.users)
        if st.button("🗑️ 确认从花名册移除", use_container_width=True):
            if user_to_del != "请选择...":
                st.session_state.users.remove(user_to_del)
                save_data(USERS_FILE, st.session_state.users)
                st.success(f"🗑️ 已将【{user_to_del}】从花名册移除。")
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
        global_missing = []
        for kw in kws:
            has_kw = any(kw in item or item in kw for item in stock_items)
            if has_kw: st.success(f"🟩 冰箱已有：**{kw}**")
            else: 
                st.error(f"🟥 冰箱缺失：**{kw}**")
                global_missing.append(kw)
        
        # 🌟 推荐升级：生成本道菜的微信采购清单文字
        if global_missing:
            st.markdown("**📋 微信备忘采购清单：**")
            wx_text = f"今日做【{dish_to_look}】还差这些食材，顺路帮忙买一下：\n👉 " + "、".join(global_missing)
            st.text_area("直接复制发到微信群：", value=wx_text, height=70)

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
            st.success(f"📦 成功入库：{exp_item}")
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
    all_today_missing = [] # 用于收集今天所有订单的总缺口
    
    for order in st.session_state.orders:
        dish = order["dish"]
        qty = order["qty"]
        detail_str = f"👤 {order['name']} ({qty}份) 💡 要求: {order['note']}"
        if dish not in summary_dict: summary_dict[dish] = {"total_qty": 0, "details": []}
        summary_dict[dish]["total_qty"] += qty
        summary_dict[dish]["details"].append(detail_str)
        
        # 顺便收集总缺口数据
        _, missing_kws = check_stock_status(dish, qty)
        all_today_missing.extend(missing_kws)
    
    # 渲染合单看版
    for dish_name, info in summary_dict.items():
        st.markdown(f"#### 🍲 **{dish_name}** ×  == `{info['total_qty']} 份` ==")
        for det in info["details"]: st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; • {det}")
        st.divider()
    
    # 🌟 推荐升级：一键生成今天全家总订单的微信群合并采购备忘录
    unique_missing = list(set(all_today_missing))
    if unique_missing:
        with st.expander("🛒 🍱 今日全家总动员·微信群合并采购备忘录"):
            total_wx_text = f"📢 报告各位！今晚掌勺总共缺少以下食材，谁下班路过菜市场帮忙捎带一下：\n" + "\n".join([f"• {m}" for m in unique_missing])
            st.text_area("全选复制发送到相亲相爱一家人微信群：", value=total_wx_text, height=110)

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

# ================= 5. 最下方：智能仓储明细大屏 =================
st.divider()
st.header("⏳ 📊 智能仓储明细大屏")
tab1, tab2 = st.tabs(["🚦 冰箱实体库存清单", "📂 时光机历史档案"])

with tab1:
    if not st.session_state.stock: 
        st.caption("冰箱目前处于清空状态。")
    else:
        st.markdown("**👇 当前冰箱小仓库明细（按天数智能分级）：**")
        today = datetime.date.today()
        
        for idx, s in enumerate(st.session_state.stock):
            try:
                b_date = datetime.datetime.strptime(s['buy_date'], "%Y-%m-%d").date()
                days_saved = (today - b_date).days
                if days_saved < 0: days_saved = 0
                
                # 🌟 推荐升级：根据天数打上不同级别的资产情况标签
                if days_saved <= 3:
                    time_tag = f"🟩 `[🥬 新鲜入库: {days_saved}天]`"
                elif days_saved <= 7:
                    time_tag = f"🟨 `[⚠️ 存货注意: {days_saved}天]`"
                else:
                    time_tag = f"🟪 `[💀 陈年老粮: {days_saved}天]`"
            except:
                time_tag = " ⚠️ `[未知登记时间]`"
                
            st.info(f"📦 物品 #{idx+1}： **{s['item']}** | 📥 入库日期： `{s['buy_date']}` | {time_tag}")
            
        if st.button("🧹 一键强制清空冰箱"):
            st.session_state.stock = []
            save_data(STOCK_FILE, [])
            st.rerun()

with tab2:
    if st.session_state.history["orders"]:
        for h_order in st.session_state.history["orders"]:
            st.markdown(f"⏱️ `{h_order.get('date', '历史')}` | 👤 **{h_order['name']}** 曾享用了 `{h_order.get('qty', 1)}份` 🍲 **{h_order['dish']}**")
