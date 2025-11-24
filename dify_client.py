#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import time
from typing import Dict, Any, Optional

class DifyClient:
    """Dify API客户端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai", user: str = "testcase_user", timeout: int = 600):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.user = user
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def run_workflow(self, inputs: Dict[str, Any], response_mode: str = "blocking") -> Dict[str, Any]:
        """执行工作流
        
        Args:
            inputs: 输入参数字典
            response_mode: 响应模式，"blocking" 或 "streaming"
            
        Returns:
            工作流执行结果
        """
        url = f"{self.base_url}/v1/workflows/run"
        
        data = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": self.user
        }
        
        try:
            print(f"发送请求到 {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                # print(f"工作流执行成功")
                return result
            else:
                error_msg = f"工作流执行失败: {response.status_code} - {response.text}"
                # print(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"执行工作流时发生错误: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def run_workflow_streaming(self, inputs: Dict[str, Any]):
        """执行工作流（流式响应）
        
        Args:
            inputs: 输入参数字典
            
        Yields:
            流式响应数据
        """
        url = f"{self.base_url}/v1/workflows/run"
        
        data = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": self.user
        }
        
        try:
            print(f"发送请求到 {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=data, stream=True, timeout=self.timeout)
            
            if response.status_code == 200:
                # print(f"流式响应状态码: {response.status_code}")
                # print(f"响应头: {dict(response.headers)}")
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        # print(f"收到流式数据行: {line_str}")
                        
                        # 尝试不同的流式数据格式
                        if line_str.startswith('data: '):
                            try:
                                data_str = line_str[6:]  # 移除 'data: ' 前缀
                                if data_str.strip() == '[DONE]':
                                    # print("收到结束标记")
                                    break
                                data_json = json.loads(data_str)
                                # print(f"解析的JSON数据: {data_json}")
                                yield data_json
                            except json.JSONDecodeError as e:
                                print(f"JSON解析错误: {e}, 原始数据: {data_str}")
                                continue
                        elif line_str.strip():
                            # 尝试直接解析JSON（可能没有data:前缀）
                            try:
                                data_json = json.loads(line_str)
                                # print(f"直接解析的JSON数据: {data_json}")
                                yield data_json
                            except json.JSONDecodeError:
                                print(f"无法解析的行: {line_str}")
                                continue
                
                # print("流式响应处理完成")
            else:
                error_msg = f"工作流执行失败: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            # print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"执行流式工作流时发生错误: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def upload_file(self, file_path: str, file_type: str = "text/plain") -> str:
        """上传文件到Dify
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            文件ID
        """
        url = f"{self.base_url}/v1/files/upload"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            with open(file_path, 'rb') as file:
                files = {
                    'file': (file_path, file, file_type)
                }
                data = {
                    'user': self.user
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get('id')
                    print(f"文件上传成功，文件ID: {file_id}")
                    return file_id
                else:
                    error_msg = f"文件上传失败: {response.status_code} - {response.text}"
                    print(error_msg)
                    raise Exception(error_msg)
                    
        except Exception as e:
            error_msg = f"上传文件时发生错误: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

class DifyTestCaseGenerator:
    """基于Dify的测试用例生成器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai", user: str = "testcase_user", result_field: str = "resultnew", timeout: int = 600):
        self.client = DifyClient(api_key, base_url, user, timeout)
        self.result_field = result_field
    
    def _extract_field_by_path(self, data: dict, field_path: str):
        """根据字段路径提取数据
        
        Args:
            data: 数据字典
            field_path: 字段路径，如 'resultnew' 或 'data.output.result'
            
        Returns:
            提取的数据
        """
        try:
            # 分割路径
            path_parts = field_path.split('.')
            current_data = data
            
            for part in path_parts:
                if isinstance(current_data, dict) and part in current_data:
                    current_data = current_data[part]
                else:
                    return None
            
            return current_data
        except Exception:
            return None
    
    def generate_testcases(self, requirement: str, **kwargs) -> str:
        """生成测试用例
        
        Args:
            requirement: 需求描述
            **kwargs: 其他参数（如用例数量、优先级等）
            
        Returns:
            生成的测试用例
        """
        inputs = {
            "in_require": requirement,
            **kwargs
        }
        
        try:
            result = self.client.run_workflow(inputs)
            
            # 检查工作流执行状态
            if 'data' in result and 'status' in result['data']:
                if result['data']['status'] == 'partial-succeeded':
                    # 检查是否有错误输出
                    if 'outputs' in result['data']:
                        outputs = result['data']['outputs']
                        if 'text' in outputs and ('错误' in outputs['text'] or '异常' in outputs['text']):
                            error_msg = f"Dify工作流执行异常: {outputs['text']}"
                            print(error_msg)
                            raise Exception(error_msg)
            
            # 从结果中提取测试用例内容
            if 'data' in result and 'outputs' in result['data']:
                outputs = result['data']['outputs']
                
                # 首先尝试使用配置的字段路径提取
                extracted_result = self._extract_field_by_path(outputs, self.result_field)
                if extracted_result is not None:
                    return extracted_result
                
                # 如果配置的字段不存在，使用默认的提取逻辑
                if 'resultnew' in outputs:
                    return outputs['resultnew']
                elif 'testcases' in outputs:
                    return outputs['testcases']
                elif 'result' in outputs:
                    return outputs['result']
                else:
                    # 如果没有特定的输出字段，返回所有输出
                    return str(outputs)
            else:
                return str(result)
                
        except Exception as e:
            error_msg = f"生成测试用例失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def generate_testcases_streaming(self, requirement: str, **kwargs):
        """流式生成测试用例
        
        Args:
            requirement: 需求描述
            **kwargs: 其他参数
            
        Yields:
            流式生成的测试用例片段
        """
        inputs = {
            "in_require": requirement,
            **kwargs
        }
        
        try:
            has_content = False
            for chunk in self.client.run_workflow_streaming(inputs):
                if 'event' in chunk and chunk['event'] == 'text_chunk':
                    if 'data' in chunk and 'text' in chunk['data']:
                        has_content = True
                        yield chunk['data']['text']
                elif 'event' in chunk and chunk['event'] == 'workflow_finished':
                    if 'data' in chunk and 'outputs' in chunk['data']:
                        outputs = chunk['data']['outputs']
                        # 检查工作流状态
                        if 'status' in chunk['data'] and chunk['data']['status'] == 'partial-succeeded':
                            # 检查输出是否包含错误信息
                            if 'text' in outputs and ('错误' in outputs['text'] or '异常' in outputs['text']):
                                error_msg = f"Dify工作流执行异常: {outputs['text']}"
                                print(error_msg)
                                raise Exception(error_msg)
                        # 工作流完成，可以处理最终输出
                        pass
            
            # 如果没有收到任何内容，可能是流式响应有问题
            if not has_content:
                print("警告: 流式响应没有收到任何文本内容")
                        
        except Exception as e:
            error_msg = f"流式生成测试用例失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)