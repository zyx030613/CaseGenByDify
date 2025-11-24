#!/usr/bin/python
# -*- coding: utf-8 -*-
import streamlit.components.v1 as components
from configparser import ConfigParser
from pathlib import Path
import streamlit as st
from io import BytesIO
from dify_client import DifyTestCaseGenerator
import xlsxwriter
import platform
import base64
import time
import os
import re

try:
    from xmindparser import xmind_to_dict
except ImportError:
    print("XMind解析库未安装，尝试安装...")
    os.system("pip install xmindparser")
    from xmindparser import xmind_to_dict
# 移除了其他不再使用的AutoGen相关导入

# 设置页面配置
st.set_page_config(
    page_title="测试用例生成辅助工具",
    page_icon=":td:",
    layout="wide"
)

conf = ConfigParser()
pt = platform.system()
main_path = os.path.split(os.path.realpath(__file__))[0]
config_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'config.ini')


def css_init():
    st.markdown('''<style>
.edw49t12 {
    max-width: 500px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 主标题样式 */
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* 卡片样式 */
.info-card {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 按钮样式增强 */
.stButton > button {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* 输入框样式 */
.stTextArea > div > div > textarea {
    border-radius: 8px;
    border: 2px solid #e9ecef;
    transition: border-color 0.3s ease;
}

.stTextArea > div > div > textarea:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

/* 侧边栏样式 */
.css-1d391kg {
    background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

/* 成功消息样式 */
.stSuccess {
    background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
    border-radius: 8px;
}

/* 错误消息样式 */
.stError {
    background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
    border-radius: 8px;
}

/* 标签页字体大小 */
.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size: 18px !important;
    font-weight: 600 !important;
}

.stTabs [data-baseweb="tab-list"] button {
    font-size: 18px !important;
}
</style>''', unsafe_allow_html=True)


def session_init():
    if 'run_cases' not in st.session_state:
        st.session_state.run_cases = True


def main():
    if pt in ["Windows"]:
        session_init()  # session缓存初始化
        css_init()  # 前端css样式初始化
        html_init()  # 前端html布局初始化
    else:
        cs_404()
    return None


def cs_404():
    # 背景图片的网址
    img_url = 'https://img.zcool.cn/community/0156cb59439764a8012193a324fdaa.gif'

    # 修改背景样式
    st.markdown('''<span style="color: cyan"> ''' + f"不支持当前系统 {pt} 运行" + '''</span>''', unsafe_allow_html=True)
    st.markdown('''<style>.css-fg4pbf{background-image:url(''' + img_url + ''');
    background-size:100% 100%;background-attachment:fixed;}</style>''', unsafe_allow_html=True)


def img_to_bytes(img_path):
    try:
        img_bytes = Path(os.path.join(main_path, img_path)).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return encoded
    except Exception as e:
        print(f"读取图片文件失败: {str(e)}")
        # 返回一个空字符串或默认图片
        return ""


# 用例格式化
@st.cache_resource
def format_testcases(raw_output):
    cases = re.findall(r'(\|.+\|)', raw_output, re.IGNORECASE)
    new_cases = list(dict.fromkeys(cases))
    return new_cases


def html_init():
    js_code = '''
    $(document).ready(function(){
        $("footer", window.parent.document).remove()
    });
    '''
    # 引用了JQuery v2.2.4（本地文件）
    jquery_path = os.path.join(main_path, 'jquery.min.js')
    with open(jquery_path, 'r', encoding='utf-8') as f:
        jquery_content = f.read()
    components.html(f'''<script>{jquery_content}</script>
        <script>{js_code}</script>''', width=0, height=0)
    # sidebar图标
    try:
        sidebar_icon = img_to_bytes("img/Jack.png")
        if sidebar_icon:
            st.sidebar.markdown(
                '''<a href="#"><img src='data:image/png;base64,{}' class='img-fluid' width=40 height=40 target='_self'></a>'''.format(
                    sidebar_icon), unsafe_allow_html=True)
    except Exception as e:
        print(f"加载侧边栏图标失败: {str(e)}")

    # sidebar.expander
    with st.sidebar:
        expander1 = st.expander("使用说明", True)
        with expander1:
            st.markdown(
                """
            ### **使用步骤**
            ##### 1、上传文件（.txt/.xmind）或手动输入需求描述
            ##### 2、配置高级选项（用例分类占比、优先级、数量等）
            ##### 3、点击"生成测试用例"按钮
            ##### 4、下载测试用例Excel文件
            
            ### **高级选项设置**
            ##### **用例分类占比**：设置各类用例的生成比例（功能用例、边界用例、异常用例、性能/兼容性用例、回归测试用例）
            
            ### **模型配置**
            ##### **Dify工作流**：基于Dify平台的AI工作流，需要配置API密钥和服务地址
            ##### **支持文件格式**：文本文件(.txt)和思维导图文件(.xmind)
            """
            , unsafe_allow_html=True)

        expander2 = st.expander("关于", False)
        with expander2:
            st.markdown(
                """
                ###### 本工具基于Dify AI工作流平台，提供智能化测试用例生成服务
                ###### AI生成的测试用例仅供参考，实际使用时需要根据具体业务场景进行人工审核和补充
                ###### 支持多种输入格式，包括文本描述和XMind思维导图，生成结构化的Excel测试用例文档
                ###### 工具采用普通模式生成，确保稳定性和一致性
                """
            )
    # sidebar标题
    st.sidebar.markdown("---")

    try:
        # 读取配置
        conf.read(config_path, encoding='utf-8')
        
        # 移除了自动创建其他配置节的代码，现在只使用Dify配置
        
        # 确保Dify配置存在
        if 'dify' not in conf.sections():
            conf.add_section('dify')
            conf['dify'] = {
                'choice': 'True',
                'api_key': 'app-3SnIRR0RJTfEiAp3KglHRDPD',
                'base_url': 'https://api.dify.ai',
                'workflow_name': '用例生成器',
                'tokens': '4096',
                'temperature': '0.7',
                'top': '0.9',
                'user': 'testcase-user',
                'result_field': 'resultnew',
                'timeout': '600'
            }
            # 保存更新后的配置
            with open(config_path, 'w', encoding='utf-8') as f:
                conf.write(f)
    except Exception as e:
        st.error(f"读取配置文件出错: {str(e)}")
    

    
    # main主页面
    source_tab0, source_tab1 = st.tabs(["📝 用例生成", "⚙️ 模型设置"])
    
    # 设置默认模型类型为Dify
    if 'model_type' not in st.session_state:
        st.session_state.model_type = "模型"

    # Dify工作流设置
    with source_tab1:
        
        # 安全地获取Dify配置
        try:
            dify_choice = eval(conf['dify']['choice']) if 'dify' in conf.sections() and 'choice' in conf['dify'] else True
            dify_api_key_value = conf['dify']['api_key'] if 'dify' in conf.sections() and 'api_key' in conf['dify'] else 'app-3SnIRR0RJTfEiAp3KglHRDPD'
            dify_base_url_value = conf['dify']['base_url'] if 'dify' in conf.sections() and 'base_url' in conf['dify'] else 'https://api.dify.ai'
            dify_workflow_name_value = conf['dify']['workflow_name'] if 'dify' in conf.sections() and 'workflow_name' in conf['dify'] else '用例生成器'
            dify_tokens_value = int(conf['dify']['tokens']) if 'dify' in conf.sections() and 'tokens' in conf['dify'] else 4096
            dify_temperature_value = float(conf['dify']['temperature']) if 'dify' in conf.sections() and 'temperature' in conf['dify'] else 0.7
            dify_top_value = float(conf['dify']['top']) if 'dify' in conf.sections() and 'top' in conf['dify'] else 0.9
            dify_user_value = conf['dify']['user'] if 'dify' in conf.sections() and 'user' in conf['dify'] else 'testcase-user'
            dify_result_field_value = conf['dify']['result_field'] if 'dify' in conf.sections() and 'result_field' in conf['dify'] else 'resultnew'
            dify_timeout_value = int(conf['dify']['timeout']) if 'dify' in conf.sections() and 'timeout' in conf['dify'] else 600
        except (KeyError, ValueError):
            dify_choice = True
            dify_api_key_value = 'app-3SnIRR0RJTfEiAp3KglHRDPD'
            dify_base_url_value = 'https://api.dify.ai'
            dify_workflow_name_value = '用例生成器'
            dify_tokens_value = 4096
            dify_temperature_value = 0.7
            dify_top_value = 0.9
            dify_user_value = 'testcase-user'
            dify_result_field_value = 'resultnew'
            dify_timeout_value = 600
        
        dify_enabled = st.checkbox("启用模型", dify_choice)
        cols3 = st.columns([2, 2, 2])
        if dify_enabled:
            dify_api_key = cols3[0].text_input("Dify API密钥", 
                                               value=dify_api_key_value,
                                               type="password",
                                               help="应用的API密钥")
            dify_base_url = cols3[1].text_input("Dify API地址", 
                                               value=dify_base_url_value,
                                               help="服务的API地址")
            dify_workflow_name = cols3[2].text_input("工作流名称", 
                                                     value=dify_workflow_name_value,
                                                     help="工作流的名称")
            # dify_max_tokens = cols3[0].number_input("最大输出Token:",
            #                                     max_value=8192,
            #                                     min_value=0,
            #                                     value=dify_tokens_value,
            #                                     help="1个英文字符 ≈ 0.3 个 token。1 个中文字符 ≈ 0.6 个 token")
            # dify_temperature = cols3[1].number_input("随机性参数temperature:",
            #                                      max_value=2.0,
            #                                      min_value=0.0,
            #                                      value=dify_temperature_value,
            #                                      step=0.1,
            #                                      help="模型随机性参数，数字越大，生成的结果随机性越大")
            # dify_top_p = cols3[2].number_input("随机性参数top_p:",
            #                                max_value=1.0,
            #                                min_value=0.0,
            #                                value=dify_top_value,
            #                                step=0.1,
            #                                help="模型随机性参数，接近 1 时：模型几乎会考虑所有可能的词")
            dify_result_field = cols3[1].text_input("返回结果提取字段", 
                                                   value=dify_result_field_value,
                                                   help="返回的JSON中提取结果的字段名，支持JSON路径格式，如：resultnew 或 data.output.result")
            dify_timeout = cols3[2].number_input("请求超时时间(秒):",
                                                min_value=30,
                                                max_value=3600,
                                                value=dify_timeout_value,
                                                help="API请求的超时时间，单位为秒。建议设置为600秒(10分钟)以上")

        if st.button('保存配置', key="save_dify_config"):
            try:
                # 保存Dify配置
                conf['dify'] = {
                    'choice': str(dify_enabled),
                    'api_key': dify_api_key,
                    'base_url': dify_base_url,
                    'workflow_name': dify_workflow_name,
                    'user': dify_user_value,
                    'result_field': dify_result_field,
                    'timeout': str(dify_timeout)
                }

                with open(config_path, 'w', encoding='utf-8') as f:
                    conf.write(f)
                with st.spinner('保存中...'):
                    time.sleep(1)
                st.success('✅ 配置保存成功！')
                st.balloons()
            except Exception as e:
                st.error(f"保存配置时出错: {str(e)}")

    # AI交互
    with source_tab0:
        cases_rate_list = [60, 20, 20, 0, 0]
        
        # 高级选项（可折叠）
        with st.expander("⚙️ 高级选项配置", expanded=False):
            # 在生成过程中禁用复选框
            checkbox_disabled = not bool(st.session_state.run_cases)
            show_slider = st.checkbox('用例分类占比(%)', True, disabled=checkbox_disabled)
            cols6 = st.columns([2, 2])
            if show_slider:
                # 在生成过程中禁用滑块控件
                sliders_disabled = not bool(st.session_state.run_cases)
                functional_testing = cols6[0].slider("功能用例", min_value=0, max_value=100, value=55, disabled=sliders_disabled)
                boundary_testing = cols6[0].slider("边界用例", min_value=0, max_value=100, value=25, disabled=sliders_disabled)
                exception_testing = cols6[0].slider("异常用例", min_value=0, max_value=100, value=20, disabled=sliders_disabled)
                perfmon_testing = cols6[1].slider("性能/兼容性用例", min_value=0, max_value=100, value=0, disabled=sliders_disabled)
                regression_testing = cols6[1].slider("回归测试用例", min_value=0, max_value=100, value=0, disabled=sliders_disabled)
                cases_rate_list = [str(functional_testing),
                                   str(boundary_testing),
                                   str(exception_testing),
                                   str(perfmon_testing),
                                   str(regression_testing)]
            # 在生成过程中禁用这些控件
            controls_disabled = not bool(st.session_state.run_cases)
            test_priority = st.selectbox("测试优先级", ["--", "急", "高", "中", "低"], index=0, disabled=controls_disabled)
            # 添加测试用例数量控制
            test_case_count = st.number_input("生成测试用例数量",
                                              min_value=0,
                                              max_value=100,
                                              value=0,
                                              step=1,
                                              disabled=controls_disabled,
                                              help="指定需要生成的测试用例数量")

        # 文件上传区域
        st.markdown("#### 📁 需求文件上传")
        st.markdown("支持上传 `.txt` 文本文件或 `.xmind` 思维导图文件")
        upload_disabled = not bool(st.session_state.run_cases)
        uploaded_file = st.file_uploader(
            "选择需求文件", 
            type=["txt", "xmind"], 
            disabled=upload_disabled,
            help="支持TXT文本文件和XMind思维导图文件"
        )
        uploaded_text = ""
        if uploaded_file is not None:
            # 处理不同类型的文件
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'txt':
                # 处理文本文件
                uploaded_text = uploaded_file.read().decode('utf-8', 'ignore')
            elif file_extension == 'xmind':
                # 处理XMind文件
                try:
                    with st.spinner("正在解析XMind文件..."):
                        uploaded_text = parse_xmind(uploaded_file)
                    
                    if uploaded_text.startswith("XMind文件解析失败"):
                        st.error(uploaded_text)
                    else:
                        st.success("✅ XMind文件解析成功！")
                        
                        # 添加一个预览按钮
                        if st.button("预览XMind内容"):
                            with st.expander("XMind需求内容预览", expanded=True):
                                st.markdown(uploaded_text)
                        
                        # 显示统计信息
                        topics_count = len(re.findall(r'\d+\.', uploaded_text))
                        st.info(f"📊 已提取 {topics_count} 个主题节点")
                except Exception as e:
                    st.error(f"处理XMind文件时出错: {str(e)}")
                    uploaded_text = ""

        # 需求描述输入区域
        st.markdown("#### ✏️ 需求描述")
        st.markdown("请详细描述您的功能需求，描述越详细，生成的测试用例越准确")
        input_disabled = not bool(st.session_state.run_cases)
        user_input = st.text_area(
            "在此输入需求描述",
                                        height=250,
                                        value=uploaded_text,
                                        disabled=input_disabled,
                                        placeholder="请详细描述你的功能需求，例如：\n"
                                                    "开发一个用户注册功能 \n"
                                                    "1、要求用户提供用户名、密码和电子邮件，\n"
                                                    "2、用户名长度为3-20个字符，\n"
                                                    "3、密码长度至少为8个字符且必须包含数字和字母，\n"
                                                    "4、电子邮件必须是有效格式。")

        # Dify模型参数已在配置中设置，无需额外调整
        # 提示词已集成到Dify工作流中，无需在界面显示

        # 提交按钮 - 根据run_cases状态控制按钮可用性
        button_disabled = not bool(st.session_state.run_cases)
        button_text = "生成中..." if button_disabled else "🚀 生成测试用例"
        submit_button = st.button(button_text, key="generate_test_cases", disabled=button_disabled, type="primary")
        
        if submit_button:
            if bool(st.session_state.run_cases):
                st.session_state.update({"run_cases": False})
                # 处理提交
                if user_input:
                    # 显示当前使用的模型类型
                    st.write(f"当前使用的模型类型: {st.session_state.model_type}")
                    # 准备任务描述
                    if test_priority != "--" and test_case_count != 0:
                        task = f""" 
                        需求描述: {user_input}
                        测试优先级: {test_priority}
                        【重要】请严格生成 {test_case_count} 条测试用例，不多不少。
                        """
                    elif test_case_count == 0 and test_priority != "--":
                        task = f""" 
                        需求描述: {user_input}
                        测试优先级: {test_priority}
                        """
                    elif test_case_count != 0 and test_priority == "--":
                        task = f""" 
                        需求描述: {user_input}
                        【重要】请严格生成 {test_case_count} 条测试用例，不多不少。
                        """
                    else:
                        task = f""" 
                        需求描述: {user_input}
                        """

                    # 创建一个固定的容器用于显示生成内容
                    response_container = st.container()

                    # 使用Dify模型生成测试用例
                    print(f"使用模型，model_type={st.session_state.model_type}")
                    if dify_enabled:
                        if conf['dify']['api_key'] != "":
                            try:
                                # 创建Dify测试用例生成器
                                dify_generator = DifyTestCaseGenerator(
                                    api_key=conf['dify']['api_key'],
                                    base_url=conf['dify']['base_url'],
                                    user=conf['dify']['user'],
                                    result_field=conf['dify']['result_field'],
                                    timeout=dify_timeout_value
                                )
                                
                                # 使用普通模式生成测试用例
                                with response_container:
                                    placeholder = st.empty()
                                    placeholder.info("🚀 正在生成测试用例...")
                                    
                                    try:
                                        result_text = dify_generator.generate_testcases(
                                            requirement=task,
                                            functional_testing=cases_rate_list[0],
                                            boundary_testing=cases_rate_list[1],
                                            exception_testing=cases_rate_list[2],
                                            perfmon_testing=cases_rate_list[3],
                                            regression_testing=cases_rate_list[4]
                                        )
                                        placeholder.markdown(result_text)
                                    except Exception as error:
                                            placeholder.error(f"生成失败: {str(error)}")
                                            raise error
                                
                                case_list = format_testcases(result_text)
                                    
                                st.success("✅ 测试用例生成完成!")
                                if len(case_list):
                                    st.download_button(
                                        label="下载测试用例(.md)",
                                        data="\n".join(case_list),
                                        file_name="测试用例.md",
                                        mime="text/markdown",
                                        icon=":material/markdown:",
                                    )
                                    output = BytesIO()
                                    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                                    worksheet = workbook.add_worksheet()
                                    for row, case in enumerate(case_list):
                                        if case.find("--------") < 0:
                                            for col, cell in enumerate(case.split("|")):
                                                if col > 0:
                                                    if row > 1:
                                                        worksheet.write(row-1, col-1, str(cell).strip())
                                                    else:
                                                        worksheet.write(row, col-1, str(cell).strip())
                                    workbook.close()
                                    st.download_button(
                                        label="下载测试用例(.xlsx)",
                                        data=output.getvalue(),
                                        file_name="测试用例.xlsx",
                                        mime="application/vnd.ms-excel",
                                        icon=":material/download:",
                                    )
                            except Exception as e:
                                st.error(f"生成测试用例时出错: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc(), language="python")
                                # 重置状态，允许下次生成
                                st.session_state.update({"run_cases": True})
                        else:
                            st.error("请先配置Dify API密钥并保存!")
                            # 重置状态，允许下次生成
                            st.session_state.update({"run_cases": True})
                    else:
                        st.error("请先启用Dify模型!")
                        # 重置状态，允许下次生成
                        st.session_state.update({"run_cases": True})
                    st.session_state.update({"run_cases": True})
                elif submit_button and not user_input:
                    st.error("请输入需求描述")
                    # 重置状态，允许下次生成
                    st.session_state.update({"run_cases": True})
            else:
                st.warning("正在生成测试用例中，请不要频繁操作！")
    return None

# 解析XMind文件，提取需求内容
def parse_xmind(xmind_file):
    try:
        # 将上传的文件保存到临时文件
        temp_file = "temp_xmind.xmind"
        with open(temp_file, "wb") as f:
            f.write(xmind_file.getbuffer())
        
        # 解析XMind文件
        xmind_content = xmind_to_dict(temp_file)
        
        # 删除临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # 提取需求文本
        requirements_text = ""
        all_paths = []  # 存储所有完整路径
        
        # 递归函数，用于提取XMind中的所有节点文本并生成完整路径
        def extract_topics(topic, path=[]):
            nonlocal all_paths
            if not topic:
                return
                
            # 获取当前节点标题
            current_title = ""
            if 'title' in topic:
                title_text = topic['title']
                
                # 处理标签
                if 'labels' in topic and topic['labels']:
                    labels = ", ".join([f"#{label}" for label in topic['labels']])
                    title_text += f" ({labels})"
                
                # 处理优先级标记
                if 'markers' in topic:
                    for marker in topic.get('markers', []):
                        if 'markerId' in marker:
                            marker_id = marker['markerId']
                            if 'priority' in marker_id:
                                # 提取优先级数字 (如 priority-1, priority-2 等)
                                priority_num = marker_id.split('-')[-1]
                                title_text += f" [优先级:{priority_num}]"
                
                current_title = title_text
            
            # 构建当前路径
            current_path = path + [current_title] if current_title else path
            
            # 处理子主题
            has_subtopics = 'topics' in topic and topic.get('topics')
            if has_subtopics:
                for subtopic in topic.get('topics', []):
                    extract_topics(subtopic, current_path)
            else:
                # 如果没有子主题，这是一个叶子节点，添加完整路径
                if current_path:
                    path_str = " - ".join(current_path)
                    all_paths.append(path_str)
                    
                    # 处理备注
                    if 'note' in topic and topic['note']:
                        if isinstance(topic['note'], dict) and 'plain' in topic['note']:
                            note_text = topic['note']['plain'].strip()
                            if note_text:
                                all_paths.append(f"{path_str} (备注: {note_text})")
                    
                    # 处理超链接
                    if 'href' in topic and topic['href']:
                        all_paths.append(f"{path_str} (链接: {topic['href']})")
        # print(f"xmind_content: {xmind_content}")
        # 处理每个sheet
        for sheet in xmind_content:
            if 'topic' in sheet and 'title' in sheet['topic']:
                sheet_title = sheet['topic']['title']
                # 处理根主题的子主题
                if 'topics' in sheet['topic']:
                    for topic in sheet['topic'].get('topics', []):
                        extract_topics(topic, [sheet_title])
        
        # 将所有路径转换为需求文本
        if all_paths:
            requirements_text = "# 办案区刻录\n\n"
            for i, path in enumerate(all_paths, 1):
                requirements_text += f"{i}. {path}\n"
        else:
            requirements_text = "未找到有效的需求路径"
        
        return requirements_text
    except Exception as e:
        print(f"解析XMind文件出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return f"XMind文件解析失败: {str(e)}"



if __name__ == '__main__':
    main()
