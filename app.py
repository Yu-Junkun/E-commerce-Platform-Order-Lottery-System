# ============================
# 订单抽奖系统
# 系统功能：
# 1. 订单查询 - 查询特定订单是否存在于订单池中
# 2. 抽奖功能 - 实现多平台订单的随机抽奖，支持轮播展示和结果保存
# 3. 结果查询 - 查询特定订单的中奖状态，展示所有中奖记录
# 4. 订单池管理 - 提供订单池的导入、保存、重置等管理功能
#
# 使用说明：通过左侧导航栏选择功能模块，按照界面提示操作
# ============================

# 导入依赖库
import streamlit as st
import random
import pandas as pd
from datetime import datetime
import pytz
import json
import os
import hashlib
import time

# 定义持久化目录（Streamlit Cloud 专用）
PERSIST_DIR = "/mount/src/e-commerce-platform-order-lottery-system"  # 例如应用名为 "lottery-system"，则路径为 "/mount/src/lottery-system"
os.makedirs(PERSIST_DIR, exist_ok=True)  # 确保目录存在

# 定义 JSON 文件路径
WINNERS_FILE = os.path.join(PERSIST_DIR, "winners.json")
ORDER_POOL_FILE = os.path.join(PERSIST_DIR, "initial_order_pool.json")
# ============================
# 页面配置
# 设置页面标题和布局
# ============================
st.set_page_config(
    page_title="元更元®",
    page_icon="🎁",
    layout="wide"
)

# ============================
# 数据持久化函数
# 实现抽奖记录的保存和加载功能
# ============================
def load_winners():
    """从文件加载抽奖记录
    
    Returns:
        list: 抽奖记录列表，每条记录为包含订单号、平台和时间的字典
             如果文件不存在或加载失败则返回空列表
    """
    # winners_file = 'winners.json'
    winners_file = WINNERS_FILE
    if os.path.exists(winners_file):
        try:
            with open(winners_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载抽奖记录失败: {e}")
    return []

def save_winners(winners_data):
    """保存抽奖记录到文件
    
    Args:
        winners_data (list): 待保存的抽奖记录列表，每条记录为包含订单号、平台和时间的字典
        
    Returns:
        bool: 保存是否成功
    """
    # winners_file = 'winners.json'
    winners_file = WINNERS_FILE
    try:
        with open(winners_file, 'w', encoding='utf-8') as f:
            json.dump(winners_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存抽奖记录失败: {e}")
        return False

# ============================
# 安全函数
# 实现密码哈希加密功能
# ============================
def hash_password(password):
    """使用SHA-256算法将密码进行哈希加密
    
    Args:
        password (str): 原始密码字符串
        
    Returns:
        str: 密码的SHA256哈希值
    """
    return hashlib.sha256(password.encode()).hexdigest()

# 初始化密码（哈希值）
# 注意：这里直接存储哈希值，不以明文形式记录原始密码
INITIAL_PASSWORD_HASH_DRAW = st.secrets["INITIAL_PASSWORD_HASH_DRAW"]
INITIAL_PASSWORD_HASH_ORDER_MANAGEMENT = st.secrets["INITIAL_PASSWORD_HASH_ORDER_MANAGEMENT"]

# ============================
# 订单池管理函数
# ============================
def load_initial_order_pool():
    """从本地文件加载订单池初始化数据
    
    Returns:
        dict: 包含各平台订单列表的字典
    """
    initial_order_pool = ORDER_POOL_FILE
    try:
        if os.path.exists(initial_order_pool):
            with open(initial_order_pool, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"加载订单池初始化数据失败: {str(e)}")
    # 如果加载失败或文件不存在，返回默认数据
    return {
        '抖音': [],
        '天猫': [],
        '京东': [],
        '小红书': [],
        '拼多多': [],
        '微信小店': []
        }

# 保存订单池初始化数据
def save_initial_order_pool(order_pool_data):
    """将当前订单池保存为初始化数据
    
    Args:
        order_pool_data (dict): 待保存的订单池数据
        
    Returns:
        bool: 保存是否成功
    """
    try:
        # 获取当前工作目录并构建文件路径
        # current_dir = os.getcwd()
        # file_path = os.path.join(current_dir, 'initial_order_pool.json')
        file_path = ORDER_POOL_FILE
        
        # 使用绝对路径保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            # 确保数据可序列化
            if isinstance(order_pool_data, dict):
                json.dump(order_pool_data, f, ensure_ascii=False, indent=2)
                return True
            else:
                st.error("订单池数据格式错误，必须是字典类型")
                return False
    except PermissionError:
        st.error("权限错误：无法写入文件，请检查目录权限")
        return False
    except Exception as e:
        st.error(f"保存订单池初始化数据失败: {type(e).__name__} - {str(e)}")
        return False

# ============================
# 会话状态初始化
# ============================
# 初始化订单池
if 'order_pool' not in st.session_state:
    # 加载订单池初始化数据，如果不存在则使用默认数据
    st.session_state.order_pool = load_initial_order_pool()

# 初始化认证状态
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 初始化抽奖记录
if 'winners' not in st.session_state:
    st.session_state.winners = load_winners()

# 初始化本次抽奖记录标识
if 'current_draw_winners' not in st.session_state:
    st.session_state.current_draw_winners = []

# ============================
# 侧边栏导航
# ============================
with st.sidebar:
    st.title("🎁 订单抽奖系统")
    
    # 主要功能导航
    st.subheader("功能导航")
    
    # 使用session_state来管理当前选中的页面
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "order_query"
    
    # 创建侧边栏按钮导航
    if st.button("🔍 订单查询", use_container_width=True):
        st.session_state.current_page = "order_query"
    if st.button("🎯 抽奖", use_container_width=True):
        st.session_state.current_page = "draw"
    if st.button("🏆 结果查询", use_container_width=True):
        st.session_state.current_page = "results"
    if st.button("⚙️ 订单池管理", use_container_width=True):
        st.session_state.current_page = "order_pool_management"
    
    # 添加持久化特性说明
    # st.caption("Ver1.2 By 元更元®")

# ============================
# 功能1: 订单查询
# 说明: 查询特定订单是否存在于订单池中
# ============================
if st.session_state.current_page == "order_query":
    st.header("查询您的订单是否在抽奖池")
    order_input = st.text_input("请输入您的订单编号：")
    
    if st.button("查询", type="primary"):
        if not order_input.strip():
            st.warning("请输入有效的订单号：")
        else:
            found = False
            platform_name = ""
            
            # 遍历所有平台的订单池进行查询
            for platform, orders in st.session_state.order_pool.items():
                if order_input.strip() in orders:
                    found = True
                    platform_name = platform
                    break
            
            if found:
                st.success(f"🎉 恭喜！您的订单号 {order_input} 在 {platform_name} 订单池中！")
            else:
                st.error(f"❌ 抱歉，订单号 {order_input} 不在订单池中。")

# ============================
# 功能2: 抽奖功能
# 说明: 实现多平台订单的随机抽奖，支持轮播展示和结果保存
# ============================
elif st.session_state.current_page == "draw":
    st.header("抽奖功能")
    
    # 密码认证
    if not st.session_state.authenticated:
        password_input = st.text_input("请输入抽奖密码：", type="password")
        if st.button("验证密码", type="primary"):
            if hash_password(password_input) == INITIAL_PASSWORD_HASH_DRAW:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误，请重新输入")
    else:
        # 显示退出按钮
        col1, col2 = st.columns([1, 0.2])
        with col1:
            st.subheader("购物平台")
        with col2:
            if st.button("退出", type="primary", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()
        
        # 选择平台
        selected_platforms = []
        col1, col2 = st.columns(2)
        for i, platform in enumerate(list(st.session_state.order_pool.keys())):
            if i % 2 == 0:
                with col1:
                    if st.checkbox(platform, value=True, key=platform):
                        selected_platforms.append(platform)
            else:
                with col2:
                    if st.checkbox(platform, value=True, key=platform):
                        selected_platforms.append(platform)
        
        # 输入中奖订单数
        winner_count = st.number_input(
            "请输入本轮抽奖订单数：",
            min_value=1,
            max_value=100,
            value=1
        )
        
        # 初始化轮播相关状态（关键）
        # 初始化抽奖相关的会话状态
        if "is_rolling" not in st.session_state:
            st.session_state.is_rolling = False  # 是否正在轮播
        if "current_rolling_order" not in st.session_state:
            st.session_state.current_rolling_order = ("", "")  # 当前轮播的(订单号, 平台)
        if "final_winners" not in st.session_state:
            st.session_state.final_winners = []  # 已选中的中奖者列表
        
        # 计算选中平台的订单总数（包含已中奖订单）
        # 计算选中平台的订单总数
        total_orders_in_selected_platforms = 0
        for platform in selected_platforms:
            total_orders_in_selected_platforms += len(st.session_state.order_pool[platform])
        
        # 收集选中平台的所有订单（排除已中奖的订单，避免重复中奖）
        # 筛选符合条件的订单（未中奖的订单）
        eligible_orders = []
        for platform in selected_platforms:
            for order in st.session_state.order_pool[platform]:
                # 确保不会重复抽取同一订单
                if not any(winner[0] == order for winner in st.session_state.final_winners):
                    eligible_orders.append((order, platform))
        
        # 显示各种错误和警告信息
        if not selected_platforms:
            st.warning("请先选择购物平台")
        elif len(eligible_orders) == 0:
            st.error("请录入足够的平台订单")
        elif winner_count > len(eligible_orders):
            st.error("抽奖订单数不能超过可选订单数")
            
        # 按钮区域：开始轮播、选中订单、重置当前轮次
        # 抽奖控制按钮
        col_start, col_select, col_reset = st.columns(3)
        with col_start:
            # 开始抽奖按钮的禁用条件
            start_disabled = (
                st.session_state.is_rolling  # 正在轮播时禁用
                or len(eligible_orders) == 0  # 无可选订单时禁用
                or len(st.session_state.final_winners) >= winner_count  # 已抽满时禁用
                or total_orders_in_selected_platforms <= winner_count  # 选中平台订单数不足时禁用
            )
            
            # 开始抽奖按钮 - 始终显示，根据条件禁用
            if st.button("🎬 开始抽奖", use_container_width=True, disabled=start_disabled):
                if not selected_platforms:
                    st.warning("请至少选择一个平台")
                elif total_orders_in_selected_platforms <= winner_count:
                    st.error("请录入足够的平台订单")
                elif len(eligible_orders) == 0:
                    st.warning("可选订单已耗尽（所有订单均已中奖）")
                else:
                    st.session_state.is_rolling = True  # 启动轮播
                    st.rerun()  # 立即刷新状态以启动轮播
            
            

        with col_select:
            # 选中订单按钮的禁用条件：只有在轮播中才能选中
            select_disabled = not st.session_state.is_rolling
            if st.button("✅ 选中此订单", use_container_width=True, disabled=select_disabled):
                st.session_state.is_rolling = False  # 停止轮播
                if st.session_state.current_rolling_order[0]:  # 订单号有效
                    # 使用中国时区（北京时间）记录当前选中时间
                    beijing_tz = pytz.timezone('Asia/Shanghai')
                    select_time = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
                    # 保存订单号、平台和选中时间
                    st.session_state.final_winners.append((st.session_state.current_rolling_order[0], st.session_state.current_rolling_order[1], select_time))
                    st.success(f"已选中第 {len(st.session_state.final_winners)}/{winner_count} 个中奖订单！")
                st.rerun()

        with col_reset:
            # 重置按钮的禁用条件：没有选中的订单时禁用
            reset_disabled = len(st.session_state.final_winners) == 0
            if st.button("🔄 重置当前轮次", use_container_width=True, disabled=reset_disabled):
                st.session_state.final_winners = []
                st.session_state.is_rolling = False
                st.success("已重置当前轮次，可重新开始抽奖")
                st.rerun()


        # 重新计算符合条件的订单，避免状态不一致
        eligible_orders = []
        for platform in selected_platforms:
            for order in st.session_state.order_pool[platform]:
                # 确保不会重复抽取同一订单
                is_already_winner = any(winner[0] == order for winner in st.session_state.final_winners)
                if not is_already_winner:
                    eligible_orders.append((order, platform))

        # 显示已选中数量提示
        st.caption(f"已选中：{len(st.session_state.final_winners)}/{winner_count}")
        
        # 轮播显示区域（核心动画）
        roll_placeholder = st.empty()
        
        # 轮播逻辑
        if st.session_state.is_rolling and eligible_orders:
            while st.session_state.is_rolling:
                # 随机选择一个订单
                random_order = random.choice(eligible_orders)
                st.session_state.current_rolling_order = random_order
                
                # 显示当前滚动的订单
                with roll_placeholder.container():
                    st.markdown(f"""
                    <div style="text-align: center; font-size: 32px; font-weight: bold; color: #2196F3; padding: 20px; border: 2px dashed #2196F3; border-radius: 10px;">
                        正在滚动...<br><br>
                        订单号：{random_order[0]}
                    </div>""", unsafe_allow_html=True)
                
                time.sleep(0.05)  # 控制轮播速度
        elif not st.session_state.is_rolling and st.session_state.current_rolling_order[0]:
            # 显示已选中的订单（暂停时显示）
            with roll_placeholder.container():
                st.markdown(f"""
                <div style="text-align: center; font-size: 32px; font-weight: bold; color: #4CAF50; padding: 20px; border: 2px solid #4CAF50; border-radius: 10px;">
                    已选中!<br><br>
                    订单号：{st.session_state.current_rolling_order[0]}
                </div>""", unsafe_allow_html=True)
        
        # 显示中奖结果
        if st.session_state.final_winners:
            st.subheader(f"中奖订单（{len(st.session_state.final_winners)}/{winner_count}）")
            # 现在final_winners包含订单号、平台和选中时间
            winner_df = pd.DataFrame(st.session_state.final_winners, columns=['订单号', '平台', '时间'])
            st.dataframe(winner_df, use_container_width=True)
        
        # 完成抽奖处理
        if len(st.session_state.final_winners) == winner_count:
            save_results = st.checkbox("保存本次抽奖结果", value=True)
            if st.button("📌 确认完成抽奖", type="primary", use_container_width=True):
                # 使用中国时区（北京时间）
                beijing_tz = pytz.timezone('Asia/Shanghai')
                current_time = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
                if save_results:
                    # 保存中奖记录（确保已中奖的订单不会被重复添加）
                    new_winners_added = False
                    for order_num, platform, select_time in st.session_state.final_winners:
                        # 检查订单是否已经中过奖
                        if not any(winner['订单号'] == order_num for winner in st.session_state.winners):
                            st.session_state.winners.append({
                                '订单号': order_num,
                                '平台': platform,
                                '时间': select_time  # 使用选中时记录的时间
                            })
                            new_winners_added = True
                    
                    if new_winners_added:
                        if save_winners(st.session_state.winners):
                            st.success("✅ 所有中奖结果已保存！")
                        else:
                            st.warning("⚠️ 中奖结果保存失败")
                    else:
                        st.info("ℹ️ 所有选中的订单已存在于中奖记录中，无需重复保存")
                
                # 导出中奖结果
                csv = winner_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 导出本次抽奖结果",
                    data=csv,
                    file_name=f"抽奖结果_{current_time.replace(' ', '_').replace(':', '')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # 重置当前轮次状态
                st.session_state.final_winners = []
                st.session_state.current_rolling_order = ("", "")
        # 重置所有抽奖历史功能
        st.subheader("历史记录管理")
        st.warning("⚠️ 重置所有抽奖历史将清除所有现有抽奖记录，请谨慎操作！")
        
        # 使用会话状态实现确认流程
        # 初始化确认状态（如果不存在）
        if 'reset_history_confirmed' not in st.session_state:
            st.session_state.reset_history_confirmed = False
            
        # 主重置按钮
        if not st.session_state.reset_history_confirmed:
            if st.button("⚠️ 重置所有抽奖历史", type="primary"):
                st.session_state.reset_history_confirmed = True
                st.rerun()  # 刷新页面显示确认选项
        else:
            # 显示确认选项
            st.info("请确认是否要继续重置所有抽奖历史记录？")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 确认重置", type="primary", use_container_width=True):
                    # 执行重置操作
                    st.session_state.winners = []
                    st.session_state.current_draw_winners = []
                    
                    # 显示详细的操作信息
                    st.write("🔄 开始执行重置操作...")
                    
                    # 直接操作文件，确保清空
                    success = False
                    try:
                        # 获取文件的绝对路径
                        # current_dir = os.getcwd()
                        # file_path = os.path.join(current_dir, 'winners.json')
                        file_path = ORDER_POOL_FILE
                        st.write(f"📍 文件路径: {file_path}")
                        
                        # 检查文件是否存在
                        if os.path.exists(file_path):
                            st.write(f"✅ 找到文件: {file_path}")
                        else:
                            st.write(f"⚠️ 文件不存在，将创建新文件: {file_path}")
                        
                        # 直接写入空数组数据
                        st.write("📝 正在写入空数据...")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump([], f, ensure_ascii=False, indent=2)
                        st.write("✅ 数据写入完成")
                        
                        # 验证文件是否已清空
                        st.write("🔍 正在验证文件内容...")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            st.write(f"📊 验证结果: 文件包含 {len(content)} 条记录")
                            # 确保文件内容为空数组
                            if isinstance(content, list) and len(content) == 0:
                                st.success("✅ winners.json文件已成功清空")
                                success = True
                            else:
                                st.error("❌ 文件清空验证失败，文件中仍有数据")
                    except Exception as e:
                        st.error(f"❌ 清空文件时发生错误: {str(e)}")
                        st.exception(e)  # 显示完整的异常信息
                    
                    # 调用save_winners确保一致性
                    st.write("⚙️ 确保数据一致性...")
                    save_winners([])
                    
                    # 显示重置结果
                    if success:
                        st.success("✅ 所有抽奖历史记录已成功重置为空状态")
                        # 重新加载数据以验证
                        refreshed_data = load_winners()
                        st.info(f"📊 当前抽奖历史记录共有 {len(refreshed_data)} 条")
                    
                    # 重置确认状态
                    st.session_state.reset_history_confirmed = False
                    
                    # 强制刷新页面以显示空状态
                    st.rerun()
            
            with col2:
                if st.button("❌ 取消重置", type="primary", use_container_width=True):
                    st.session_state.reset_history_confirmed = False
                    st.info("已取消重置操作")
                    st.rerun()


# ============================
# 功能3: 结果查询
# 说明: 查询特定订单的中奖状态，展示所有中奖记录
# ============================
elif st.session_state.current_page == "results":
    st.header("中奖结果")
    
    # 查询订单是否中奖
    st.subheader("查询订单是否中奖")
    winner_query_input = st.text_input("请输入您的订单号：", placeholder="例如: D2023001")
    
    if st.button("查询中奖状态", type="primary"):
        if not winner_query_input.strip():
            st.warning("请输入有效的订单号")
        else:
            winner_found = False
            winner_info = None
            
            # 遍历所有历史中奖记录进行查询
            for winner in st.session_state.winners:
                if winner['订单号'] == winner_query_input.strip():
                    winner_found = True
                    winner_info = winner
                    break
            
            if winner_found:
                st.success(f"🎉 恭喜！订单号 {winner_query_input} 在 {winner_info['时间']} 中奖了！请联系 {winner_info['平台']} 平台客服兑换。")
            else:
                st.info(f"📋 抱歉，您的订单号 {winner_query_input} 暂未中奖。")
    
    # 显示所有中奖记录
    st.subheader("所有中奖记录")
    if len(st.session_state.winners) > 0:
        # 转换为DataFrame便于显示
        winners_df = pd.DataFrame(st.session_state.winners)
        
        # 按时间排序
        winners_df = winners_df.sort_values(by='时间', ascending=False)
        
        st.dataframe(winners_df)
        
        # 导出功能
        if st.button("导出中奖结果", type="primary"):
            # 转换为CSV
            csv = winners_df.to_csv(index=False, encoding='utf-8-sig')
            
            # 提供下载链接
            # 使用中国时区（北京时间）
            beijing_tz = pytz.timezone('Asia/Shanghai')
            st.download_button(
                label="📥 下载CSV文件",
                type="primary",
                data=csv,
                file_name=f"抽奖结果_{datetime.now(beijing_tz).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("暂无抽奖记录")
    
# ============================
# 功能4: 订单池管理
# 说明: 提供订单池的导入、保存、重置等管理功能
# ============================
elif st.session_state.current_page == "order_pool_management":
    st.header("⚙️ 订单池管理")
    
    # 密码认证
    if not st.session_state.get('pool_management_authenticated', False):
        password_input = st.text_input("请输入管理密码：", type="password")
        if st.button("验证密码", key="pool_management_auth", type="primary"):
            if hash_password(password_input) == INITIAL_PASSWORD_HASH_ORDER_MANAGEMENT:
                st.session_state.pool_management_authenticated = True
                st.success("密码正确，欢迎进入订单池管理功能！")
                st.rerun()
            else:
                st.error("密码错误，请重新输入")
    else:
        # 显示退出按钮
        col1, col2 = st.columns([1, 0.2])
        with col1:
            st.subheader("订单池管理功能")
        with col2:
            if st.button("退出", type="primary", use_container_width=True, key="pool_management_exit"):
                st.session_state.pool_management_authenticated = False
                st.rerun()
        
        # 显示当前订单池信息
        total_orders = sum(len(orders) for orders in st.session_state.order_pool.values())
        # 只统计订单数大于0的平台
        active_platforms = len([p for p, orders in st.session_state.order_pool.items() if len(orders) > 0])
        st.info(f"当前订单池包含 {active_platforms} 个平台，总计 {total_orders} 个订单号")
        # 显示当前订单池详细信息（可选折叠）
        with st.expander("查看当前订单池详细信息"):
            for platform, orders in st.session_state.order_pool.items():
                st.subheader(f"{platform} ({len(orders)} 个订单)")
                # 显示订单列表，每行5个
                order_text = "\n".join([", ".join(orders[i:i+5]) for i in range(0, len(orders), 5)])
                st.text(order_text)
        
        # 导入订单池功能
        st.subheader("导入订单池")
        
        # 选择导入模式：追加或替换
        import_mode = st.radio(
            "导入方式：",
            ["追加模式（保留现有数据）", "替换模式（清除现有数据）"],
            index=0
        )
        
        # 选择具体导入方式
        import_method = st.selectbox(
            "选择导入方式：",
            ["文件上传 (CSV/XLSX)", "文本输入"]
        )
        
        # 定义处理订单导入的函数
        def process_orders(platform_order_pairs):
            """处理导入的订单数据
            
            Args:
                platform_order_pairs (list): 平台和订单号的元组列表
            """
            new_orders = {}
            total_new = 0
            duplicates = 0
            errors = 0
            
            # 如果是追加模式，保留现有数据
            if import_mode == "追加模式（保留现有数据）":
                new_orders = {platform: orders.copy() for platform, orders in st.session_state.order_pool.items()}
            
            # 处理订单数据
            for platform, order in platform_order_pairs:
                try:
                    if not platform or not order:
                        errors += 1
                        continue
                    
                    # 初始化平台列表（如果不存在）
                    if platform not in new_orders:
                        new_orders[platform] = []
                    
                    # 查重去重
                    if order not in new_orders[platform]:
                        new_orders[platform].append(order)
                        total_new += 1
                    else:
                        duplicates += 1
                except Exception as e:
                    errors += 1
            
            # 更新订单池
            if total_new > 0 or (import_mode == "替换模式（清除现有数据）" and len(platform_order_pairs) > 0):
                st.session_state.order_pool = new_orders
                st.success(f"✅ 订单数据导入成功！")
                st.info(f"导入统计：\n- 新增订单数: {total_new}\n- 重复订单数: {duplicates}\n- 错误行数: {errors}")
                
                # 显示更新后的订单池信息
                updated_total = sum(len(orders) for orders in st.session_state.order_pool.values())
                st.success(f"📊 更新后订单池共有 {len(st.session_state.order_pool)} 个平台，总计 {updated_total} 个订单号")
            else:
                if errors > 0:
                    st.warning(f"⚠️ 导入过程中发现 {errors} 行错误数据，请检查格式")
                if duplicates > 0:
                    st.warning(f"⚠️ 发现 {duplicates} 个重复订单，已自动去重")
                if total_new == 0 and not (import_mode == "替换模式（清除现有数据）" and len(platform_order_pairs) > 0):
                    st.info("📋 没有新数据被导入")
        
        # 文件上传方式
        # 文件上传导入功能
        if import_method == "文件上传 (CSV/XLSX)":
            st.info("支持CSV和XLSX文件格式，文件需要包含'平台'和'主订单编号'两列数据")
            uploaded_file = st.file_uploader("选择CSV或XLSX文件：", type=["csv", "xlsx"])
            
            if uploaded_file is not None:
                try:
                    # 根据文件类型选择对应的读取方法
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                    else:  # xlsx
                        df = pd.read_excel(uploaded_file)
                    
                    # 验证文件格式是否符合要求
                    if '平台' not in df.columns or '主订单编号' not in df.columns:
                        st.error("❌ 文件格式不正确！请确保文件包含'平台'和'主订单编号'两列")
                    else:
                        # 显示文件预览信息
                        st.success(f"📊 成功读取文件，共 {len(df)} 条数据")
                        st.dataframe(df.head(10))  # 显示前10行预览
                        
                        # 点击导入按钮处理数据
                        if st.button("从文件导入订单", type="primary"):
                            # 处理数据
                            platform_order_pairs = list(zip(df['平台'].astype(str), df['主订单编号'].astype(str)))
                            process_orders(platform_order_pairs)
                except Exception as e:
                    st.error(f"❌ 读取文件失败: {str(e)}")
        
        # 文本输入方式
        # 文本输入导入功能
        else:
            st.info("请按照 '平台,主订单编号' 的格式，每行输入一条记录进行导入")
            st.info("例如：抖音,D2023001\n天猫,T2023002")
            
            # 文本输入区域
            import_text = st.text_area("请输入订单数据：", height=200, placeholder="平台,主订单编号\n平台,主订单编号\n...")
            
            # 导入按钮
            if st.button("导入订单数据", type="primary"):
                if not import_text.strip():
                    st.warning("请输入订单数据后再进行导入")
                else:
                    # 处理输入的文本数据
                    platform_order_pairs = []
                    lines = import_text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            # 分割平台和订单号（使用第一个逗号作为分隔符）
                            parts = line.split(',', 1)
                            if len(parts) == 2:
                                platform = parts[0].strip()
                                order = parts[1].strip()
                                platform_order_pairs.append((platform, order))
                        except Exception as e:
                            pass  # 错误行会在process_orders中统计
                    
                    if platform_order_pairs:
                        process_orders(platform_order_pairs)
                    else:
                        st.warning("未找到有效数据，请检查输入格式")
        # 保存为初始化数据功能
        st.subheader("保存为初始化数据")
        st.info("将当前订单池保存为初始化数据，应用重启后将自动加载此数据")
        
        # 初始化确认状态（避免重复确认）
        if 'confirm_save' not in st.session_state:
            st.session_state.confirm_save = False
        
        # 确认保存流程 - 首次点击阶段
        if not st.session_state.confirm_save:
            if st.button("保存为初始化数据", type="primary", key="save_initial_btn"):
                st.session_state.confirm_save = True
                # 使用rerun来立即更新UI状态
                st.rerun()
        else:
            # 第二步：显示确认信息和确认按钮
            st.warning("⚠️ 确定要将当前订单池保存为初始化数据吗？此操作会覆盖现有的初始化数据！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认保存", type="primary", key="confirm_save_btn", use_container_width=True):
                    # 执行保存操作
                    if save_initial_order_pool(st.session_state.order_pool):
                        st.success("✅ 订单池已成功保存为初始化数据")
                        # 保存成功后，从文件重新加载初始数据以更新显示
                        refreshed_data = load_initial_order_pool()
                        # 只统计订单数大于0的平台
                        active_platforms = len([p for p, orders in refreshed_data.items() if len(orders) > 0])
                        st.info(f"📊 重新加载的初始化数据包含 {active_platforms} 个活跃平台（订单数>0）")
                        # 显示重新加载的数据概要
                        total_orders = sum(len(orders) for orders in refreshed_data.values())
                        st.info(f"初始化数据共有 {total_orders} 个订单")
                    else:
                        st.error("❌ 保存失败，请稍后重试")
                    
                    st.session_state.confirm_save = False
            with col2:
                if st.button("❌ 取消保存", type="primary", key="cancel_save_btn", use_container_width=True):
                    # 取消保存，重置确认状态
                    st.session_state.confirm_save = False
                    # 使用rerun来立即更新UI状态
                    st.rerun()

        # 重置订单池功能
        st.subheader("重置订单池")
        st.warning("⚠️ 重置订单池将清除所有现有订单信息，请谨慎操作！")
        
        # 初始化确认状态（避免重复确认）
        if 'reset_confirmed' not in st.session_state:
            st.session_state.reset_confirmed = False
        
        # 确认重置流程 - 首次点击阶段
        if not st.session_state.reset_confirmed:
            if st.button("⚠️ 重置订单池", type="primary"):
                st.session_state.reset_confirmed = True
                st.rerun()  # 刷新页面显示确认选项
        else:
            # 显示确认选项
            st.info("请确认是否要继续重置订单池操作？")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 确认重置", type="primary", use_container_width=True):
                    # 执行重置操作
                    # 创建包含所有平台但订单为空的订单池
                    empty_order_pool = {
                        '抖音': [],
                        '天猫': [],
                        '京东': [],
                        '小红书': [],
                        '拼多多': [],
                        '微信小店': []
                    }
                    
                    # 显示详细的操作信息
                    st.write("🔄 开始执行重置操作...")
                    
                    # 直接操作文件，确保清空
                    success = False
                    try:
                        # 获取文件的绝对路径
                        current_dir = os.getcwd()
                        file_path = os.path.join(current_dir, 'initial_order_pool.json')
                        st.write(f"📍 文件路径: {file_path}")
                        
                        # 检查文件是否存在
                        if os.path.exists(file_path):
                            st.write(f"✅ 找到文件: {file_path}")
                        else:
                            st.write(f"⚠️ 文件不存在，将创建新文件: {file_path}")
                        
                        # 直接写入空订单池数据
                        st.write("📝 正在写入空订单池数据...")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(empty_order_pool, f, ensure_ascii=False, indent=2)
                        st.write("✅ 数据写入完成")
                        
                        # 验证文件是否已清空
                        st.write("🔍 正在验证文件内容...")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                            st.write(f"📊 验证结果: 文件包含 {len(content)} 个平台")
                            # 确保所有平台都存在且订单列表为空
                            if isinstance(content, dict) and all(len(orders) == 0 for orders in content.values()):
                                st.success("✅ initial_order_pool.json文件已成功清空")
                                success = True
                            else:
                                st.error("❌ 文件清空验证失败，文件中仍有数据")
                    except Exception as e:
                        st.error(f"❌ 清空文件时发生错误: {str(e)}")
                        st.exception(e)  # 显示完整的异常信息
                    
                    # 更新session_state
                    st.write("⚙️ 更新应用状态...")
                    st.session_state.order_pool = empty_order_pool
                    
                    # 显示重置结果
                    if success:
                        st.success("✅ 订单池已成功重置为空状态")
                        # 重新加载数据以验证
                        refreshed_data = load_initial_order_pool()
                        total_orders = sum(len(orders) for orders in refreshed_data.values())
                        st.info(f"📊 当前订单池共有 {total_orders} 个订单")
                    
                    # 重置确认状态
                    st.session_state.reset_confirmed = False
                    
                    # 强制刷新页面以显示空订单池状态
                    st.rerun()
            
            with col2:
                if st.button("❌ 取消重置", type="primary", use_container_width=True):
                    st.session_state.reset_confirmed = False
                    st.info("已取消重置操作")
                    st.rerun()    
        
        


