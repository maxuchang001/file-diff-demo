import xml.etree.ElementTree as ET
import pandas as pd
import graphviz
import os
import matplotlib.pyplot as plt  # 新增导入
from datetime import datetime  # 用于添加时间戳
from collections import defaultdict
import base64  # 新增导入
import uuid  # 用于生成唯一标识符
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import json

# 设置 Graphviz 可执行文件路径
graphviz.backend.dot_command.DOT_BINARY = r"C:\Program Files\Graphviz\bin\dot.exe"


def get_temp_filename(prefix, suffix):
    """生成带时间戳和唯一标识符的临时文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}{suffix}"


def image_to_base64(image_path):
    """将图片文件转换为base64字符串"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            # 根据文件扩展名确定MIME类型
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
            }.get(ext, "image/png")
            return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None


def image_to_base64_from_memory(image_data):
    """将内存中的图片数据转换为base64字符串"""
    try:
        encoded_string = base64.b64encode(image_data).decode("utf-8")
        return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(f"Error converting image to base64 from memory: {e}")
        return None


def generate_graphviz_image(dot, format="png"):
    """直接在内存中生成图片数据"""
    try:
        # 使用BytesIO作为内存缓冲区
        image_data = dot.pipe(format=format)
        return image_data
    except Exception as e:
        print(f"Error generating graphviz image in memory: {e}")
        return None


def generate_matplotlib_image(fig):
    """直接在内存中生成matplotlib图片数据"""
    try:
        # 使用BytesIO作为内存缓冲区
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Error generating matplotlib image in memory: {e}")
        return None


class IPXACTVisualizer:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.ns = {
            "spirit": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014"
        }
        self.xml_file = xml_file
        print(f"Processing XML file: {xml_file}")

    def generate_module_diagram(self, output_img="module_diagram"):
        components = [
            elem.find("spirit:name", self.ns).text
            for elem in self.root.findall(".//spirit:componentInstance", self.ns)
        ]
        connections = [
            elem.find("spirit:name", self.ns).text
            for elem in self.root.findall(".//spirit:interconnection", self.ns)
        ]

        if not components:
            print("No components found in XML")
            return None

        dot = graphviz.Digraph(comment="Module Diagram", engine="dot")
        for c in components:
            dot.node(c)
        if len(components) >= 2:
            dot.edge(components[0], components[1])

        # 直接在内存中生成图片
        image_data = generate_graphviz_image(dot)
        if image_data:
            return image_to_base64_from_memory(image_data)
        return None

    def generate_register_table(self):
        registers = []
        for reg in self.root.findall(".//spirit:register", self.ns):
            name = reg.find("spirit:name", self.ns).text
            addr = reg.find("spirit:addressOffset", self.ns).text
            registers.append({"Register Name": name, "Address Offset": addr})
        if registers:
            df = pd.DataFrame(registers)
            fig, ax = plt.subplots(figsize=(6, 0.5 + 0.4 * len(df)))
            ax.axis("off")
            table = ax.table(
                cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
            plt.tight_layout()

            # 直接在内存中生成图片
            image_data = generate_matplotlib_image(fig)
            plt.close(fig)

            if image_data:
                return image_to_base64_from_memory(image_data)
        print("No registers found in XML")
        return None

    def generate_parameter_table(self):
        params = []
        for param in self.root.findall(".//spirit:parameter", self.ns):
            name = param.find("spirit:name", self.ns).text
            value = param.find("spirit:value", self.ns).text
            params.append({"Parameter": name, "Value": value})
        if params:
            df = pd.DataFrame(params)
            fig, ax = plt.subplots(figsize=(6, 0.5 + 0.4 * len(df)))
            ax.axis("off")
            table = ax.table(
                cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
            plt.tight_layout()

            # 直接在内存中生成图片
            image_data = generate_matplotlib_image(fig)
            plt.close(fig)

            if image_data:
                return image_to_base64_from_memory(image_data)
        print("No parameters found in XML")
        return None

    def generate_interface_view(self):
        interfaces = []
        for intf in self.root.findall(".//spirit:busInterface", self.ns):
            name = intf.find("spirit:name", self.ns).text
            bus_type_elem = intf.find("spirit:busType", self.ns)
            bus_type = (
                bus_type_elem.get("spirit:name")
                if bus_type_elem is not None
                else "Unknown"
            )
            interfaces.append({"Interface Name": name, "Bus Type": bus_type})

        if interfaces:
            df = pd.DataFrame(interfaces)
            fig, ax = plt.subplots(figsize=(6, 0.5 + 0.4 * len(df)))
            ax.axis("off")
            table = ax.table(
                cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.5)
            plt.tight_layout()

            # 直接在内存中生成图片
            image_data = generate_matplotlib_image(fig)
            plt.close(fig)

            if image_data:
                return image_to_base64_from_memory(image_data)
        print("No interfaces found in XML")
        return None

    def extract_ipxact_elements(self, root):
        """提取所有常见IPXACT元素"""
        elements = {
            "component": [],
            "parameter": [],
            "businterface": [],
            "memorymap": [],
            "register": [],
            "field": [],
            "fileset": [],
            "view": [],
            "port": [],
            "componentinstance": [],
            "adhocconnection": [],
            "choice": [],
            "vendorextension": [],
            "busdefinition": [],
            "design": [],
            "addressspace": [],
        }
        ns = self.ns

        # component - 修改XPath表达式
        comp = root  # 根元素就是component
        if comp is not None:
            elements["component"].append(
                {
                    "name": comp.findtext("spirit:name", default="N/A", namespaces=ns),
                    "version": comp.findtext(
                        "spirit:version", default="N/A", namespaces=ns
                    ),
                    "vendor": comp.findtext(
                        "spirit:vendor", default="N/A", namespaces=ns
                    ),
                    "library": comp.findtext(
                        "spirit:library", default="N/A", namespaces=ns
                    ),
                }
            )

        # 提取总线定义信息
        for bus in root.findall(".//spirit:busDefinition", ns):
            bus_data = {
                "name": bus.findtext("spirit:name", default="N/A", namespaces=ns),
                "version": bus.findtext("spirit:version", default="N/A", namespaces=ns),
                "directConnection": bus.findtext(
                    "spirit:directConnection", default="N/A", namespaces=ns
                ),
                "isAddressable": bus.findtext(
                    "spirit:isAddressable", default="N/A", namespaces=ns
                ),
            }
            elements["busdefinition"].append(bus_data)

        # 提取地址空间信息
        for space in root.findall(".//spirit:addressSpace", ns):
            space_data = {
                "name": space.findtext("spirit:name", default="N/A", namespaces=ns),
                "range": space.findtext("spirit:range", default="N/A", namespaces=ns),
                "width": space.findtext("spirit:width", default="N/A", namespaces=ns),
                "addressblocks": [],
            }

            # 提取地址块
            for block in space.findall(".//spirit:addressBlock", ns):
                block_data = {
                    "name": block.findtext("spirit:name", default="N/A", namespaces=ns),
                    "baseAddress": block.findtext(
                        "spirit:baseAddress", default="N/A", namespaces=ns
                    ),
                    "range": block.findtext(
                        "spirit:range", default="N/A", namespaces=ns
                    ),
                    "width": block.findtext(
                        "spirit:width", default="N/A", namespaces=ns
                    ),
                }
                space_data["addressblocks"].append(block_data)

            elements["addressspace"].append(space_data)

        # 提取设计信息
        for design in root.findall(".//spirit:design", ns):
            design_data = {
                "name": design.findtext("spirit:name", default="N/A", namespaces=ns),
                "version": design.findtext(
                    "spirit:version", default="N/A", namespaces=ns
                ),
                "componentinstances": [],
            }

            # 提取组件实例
            for ci in design.findall(".//spirit:componentInstance", ns):
                ci_data = {
                    "name": ci.findtext("spirit:name", default="N/A", namespaces=ns),
                    "componentRef": (
                        ci.find("spirit:componentRef", ns).get(f"{{{ns['spirit']}}}name")
                        if ci.find("spirit:componentRef", ns) is not None
                        else "N/A"
                    ),
                    "version": (
                        ci.find("spirit:componentRef", ns).get(f"{{{ns['spirit']}}}version")
                        if ci.find("spirit:componentRef", ns) is not None
                        else "N/A"
                    ),
                }
                design_data["componentinstances"].append(ci_data)

            elements["design"].append(design_data)

        # parameters
        for param in root.findall(".//spirit:parameter", ns):
            elements["parameter"].append(
                {
                    "name": param.findtext("spirit:name", default="N/A", namespaces=ns),
                    "value": param.findtext(
                        "spirit:value", default="N/A", namespaces=ns
                    ),
                    "type": param.findtext("spirit:type", default="N/A", namespaces=ns),
                }
            )
        # busInterfaces
        for intf in root.findall(".//spirit:busInterface", ns):
            bus_type = intf.find("spirit:busType", ns)
            bus_type_name = (
                bus_type.get(f"{{{ns['spirit']}}}name") if bus_type is not None else "N/A"
            )
            elements["businterface"].append(
                {
                    "name": intf.findtext("spirit:name", default="N/A", namespaces=ns),
                    "type": bus_type_name,
                    "mode": "master"
                    if intf.find("spirit:master", ns) is not None
                    else "slave",
                }
            )
        # memoryMaps
        for mm in root.findall(".//spirit:memoryMap", ns):
            mm_name = mm.findtext("spirit:name", default="N/A", namespaces=ns)
            mm_data = {"name": mm_name, "addressblocks": []}
            # 提取address blocks
            for ab in mm.findall(".//spirit:addressBlock", ns):
                ab_data = {
                    "name": ab.findtext("spirit:name", default="N/A", namespaces=ns),
                    "baseAddress": ab.findtext(
                        "spirit:baseAddress", default="N/A", namespaces=ns
                    ),
                    "range": ab.findtext("spirit:range", default="N/A", namespaces=ns),
                    "width": ab.findtext("spirit:width", default="N/A", namespaces=ns),
                }
                mm_data["addressblocks"].append(ab_data)
            elements["memorymap"].append(mm_data)
        # registers
        for reg in root.findall(".//spirit:register", ns):
            reg_data = {
                "name": reg.findtext("spirit:name", default="N/A", namespaces=ns),
                "address": reg.findtext(
                    "spirit:addressOffset", default="N/A", namespaces=ns
                ),
                "size": reg.findtext("spirit:size", default="N/A", namespaces=ns),
                "access": reg.findtext("spirit:access", default="N/A", namespaces=ns),
                "fields": [],
            }
            # 提取字段信息
            for field in reg.findall(".//spirit:field", ns):
                field_data = {
                    "name": field.findtext("spirit:name", default="N/A", namespaces=ns),
                    "bitOffset": field.findtext(
                        "spirit:bitOffset", default="N/A", namespaces=ns
                    ),
                    "bitWidth": field.findtext(
                        "spirit:bitWidth", default="N/A", namespaces=ns
                    ),
                    "access": field.findtext(
                        "spirit:access", default="N/A", namespaces=ns
                    ),
                }
                reg_data["fields"].append(field_data)
            elements["register"].append(reg_data)
        # fileSets
        for fs in root.findall(".//spirit:fileSet", ns):
            elements["fileset"].append(
                {"name": fs.findtext("spirit:name", default="N/A", namespaces=ns)}
            )
        # views
        for view in root.findall(".//spirit:view", ns):
            elements["view"].append(
                {
                    "name": view.findtext("spirit:name", default="N/A", namespaces=ns),
                    "envIdentifier": view.findtext(
                        "spirit:envIdentifier", default="N/A", namespaces=ns
                    ),
                }
            )
        # ports
        for port in root.findall(".//spirit:port", ns):
            elements["port"].append(
                {
                    "name": port.findtext("spirit:name", default="N/A", namespaces=ns),
                    "direction": port.findtext(
                        "spirit:wire/spirit:direction", default="N/A", namespaces=ns
                    ),
                }
            )
        # componentInstances
        for inst in root.findall(".//spirit:componentInstance", ns):
            type_elem = inst.find("spirit:componentRef", ns)
            type_name = (
                type_elem.get(f"{{{ns['spirit']}}}name")
                if type_elem is not None
                else "N/A"
            )
            elements["componentinstance"].append(
                {
                    "name": inst.findtext("spirit:name", default="N/A", namespaces=ns),
                    "componentRef": type_name,
                }
            )
        # adhocConnections
        for conn in root.findall(".//spirit:adHocConnection", ns):
            conn_data = {
                "name": conn.findtext("spirit:name", default="N/A", namespaces=ns),
                "internalPortReferences": [],
            }
            for ref in conn.findall(".//spirit:internalPortReference", ns):
                ref_data = {
                    "componentRef": ref.get(f"{{{ns['spirit']}}}componentRef", "N/A"),
                    "portRef": ref.get(f"{{{ns['spirit']}}}portRef", "N/A"),
                }
                conn_data["internalPortReferences"].append(ref_data)
            elements["adhocconnection"].append(conn_data)
        # choices
        for choice in root.findall(".//spirit:choice", ns):
            elements["choice"].append(
                {
                    "name": choice.findtext(
                        "spirit:name", default="N/A", namespaces=ns
                    ),
                    "value": choice.findtext(
                        "spirit:value", default="N/A", namespaces=ns
                    ),
                }
            )
        # vendorExtensions
        for ext in root.findall(".//spirit:vendorExtension", ns):
            elements["vendorextension"].append(
                {"name": ext.findtext("spirit:name", default="N/A", namespaces=ns)}
            )
        return elements

    def generate_component_instances_diff_diagram(
        self, elements1, elements2, output_img="comp_inst_diff"
    ):
        """生成组件实例差异图"""
        try:
            # 提取节点信息
            nodes1 = {item["name"]: item for item in elements1["componentinstance"]}
            nodes2 = {item["name"]: item for item in elements2["componentinstance"]}

            # 创建图
            dot = graphviz.Digraph(comment="Component Instances Diff", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加节点
            for name in set(nodes1.keys()) | set(nodes2.keys()):
                if name in nodes1 and name in nodes2:
                    if nodes1[name] != nodes2[name]:
                        # 修改的节点 - 使用#ffffa6
                        dot.node(
                            name,
                            f"{name}\n({nodes1[name]['componentRef']} → {nodes2[name]['componentRef']})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffa6",
                        )
                    else:
                        # 未修改的节点 - 使用#ffffff
                        dot.node(
                            name,
                            f"{name}\n({nodes1[name]['componentRef']})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff",
                        )
                elif name in nodes1:
                    # 删除的节点 - 使用#ffa6a6
                    dot.node(
                        name,
                        f"{name}\n({nodes1[name]['componentRef']})",
                        shape="box",
                        style="filled",
                        fillcolor="#ffa6a6",
                    )
                else:
                    # 新增的节点 - 使用#a6ffa6
                    dot.node(
                        name,
                        f"{name}\n({nodes2[name]['componentRef']})",
                        shape="box",
                        style="filled",
                        fillcolor="#a6ffa6",
                    )

            # 提取连接关系
            connections1 = set()
            connections2 = set()

            # 从第一个XML中提取连接
            for conn in self.root.findall(".//spirit:adHocConnection", self.ns):
                refs = conn.findall("spirit:internalPortReference", self.ns)
                if len(refs) >= 2:
                    comp1 = refs[0].get(f"{{{self.ns['spirit']}}}componentRef")
                    comp2 = refs[1].get(f"{{{self.ns['spirit']}}}componentRef")
                    if comp1 and comp2 and comp1 in nodes1 and comp2 in nodes1:
                        # 保持原始连接方向
                        connections1.add((comp1, comp2))

            # 使用elements2中的连接信息
            for conn in elements2.get("adhocconnection", []):
                refs = conn.get("internalPortReferences", [])
                if len(refs) >= 2:
                    comp1 = refs[0].get("componentRef")
                    comp2 = refs[1].get("componentRef")
                    if comp1 and comp2 and comp1 in nodes2 and comp2 in nodes2:
                        # 保持原始连接方向
                        connections2.add((comp1, comp2))

            # 添加连接
            # 1. 添加在两个版本中都存在的连接
            common_connections = connections1 & connections2
            for comp1, comp2 in common_connections:
                dot.edge(comp1, comp2, color="#ffffff", style="solid")

            # 2. 添加只在新版本中存在的连接
            new_connections = connections2 - connections1
            for comp1, comp2 in new_connections:
                dot.edge(comp1, comp2, color="#a6ffa6", style="solid")

            # 3. 添加只在旧版本中存在的连接
            old_connections = connections1 - connections2
            for comp1, comp2 in old_connections:
                dot.edge(comp1, comp2, color="#ffa6a6", style="solid")

            # 4. 添加被删除节点与其他节点的连接
            # 只处理那些不在old_connections中的连接
            for old_node in set(nodes1.keys()) - set(nodes2.keys()):
                for common_node in set(nodes1.keys()) & set(nodes2.keys()):
                    # 检查是否存在连接，考虑两个方向
                    if (old_node, common_node) in connections1 and (
                        old_node,
                        common_node,
                    ) not in old_connections:
                        dot.edge(old_node, common_node, style="solid", color="#ffa6a6")
                    elif (common_node, old_node) in connections1 and (
                        common_node,
                        old_node,
                    ) not in old_connections:
                        dot.edge(common_node, old_node, style="solid", color="#ffa6a6")

            dot.format = "png"
            output_path = os.path.splitext(output_img)[0]
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"
            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating component instances diff diagram: {e}")
            return None

    def generate_bus_interfaces_diff_diagram(self, elements1, elements2, output_img="bus_intf_diff"):
        """生成总线接口差异图"""
        try:
            # 提取节点信息
            interfaces1 = []
            interfaces2 = []
            
            # 从第一个XML中提取接口信息
            for intf in self.root.findall(".//spirit:busInterface", self.ns):
                name = intf.findtext("spirit:name", default="N/A", namespaces=self.ns)
                bus_type = intf.find("spirit:busType", self.ns)
                bus_type_name = (
                    bus_type.get(f"{{{self.ns['spirit']}}}name") if bus_type is not None else "N/A"
                )
                mode = (
                    "master"
                    if intf.find("spirit:master", self.ns) is not None
                    else "slave"
                )
                interfaces1.append((name, bus_type_name, mode))

            # 从第二个XML中提取接口信息
            for intf in elements2.get("businterface", []):
                name = intf.get("name", "N/A")
                # 修正：使用正确的字段名获取总线类型
                bus_type = intf.get("type", "N/A")
                if bus_type == "N/A":
                    # 如果type字段为空，尝试从busType字段获取
                    bus_type = intf.get("busType", "N/A")
                mode = intf.get("mode", "N/A")
                interfaces2.append((name, bus_type, mode))

            # 创建图
            dot = graphviz.Digraph(comment="Bus Interfaces Diff", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加节点
            for name, bus_type, mode in interfaces1:
                # 检查节点是否在第二个版本中存在
                found_in_v2 = False
                changed = False
                for name2, bus_type2, mode2 in interfaces2:
                    if name == name2:
                        found_in_v2 = True
                        if bus_type != bus_type2 or mode != mode2:
                            changed = True
                        break

                if not found_in_v2:
                    # 删除的节点 - 红色
                    dot.node(
                        name,
                        f"{name}\n({bus_type})\n{mode}",
                        shape="box",
                        style="filled",
                        fillcolor="#ffa6a6"
                    )
                elif changed:
                    # 修改的节点 - 黄色
                    dot.node(
                        name,
                        f"{name}\n({bus_type})\n{mode}",
                        shape="box",
                        style="filled",
                        fillcolor="#ffffa6"
                    )
                else:
                    # 未修改的节点 - 白色
                    dot.node(
                        name,
                        f"{name}\n({bus_type})\n{mode}",
                        shape="box",
                        style="filled",
                        fillcolor="#ffffff"
                    )

            # 添加第二个版本中的新节点
            for name, bus_type, mode in interfaces2:
                found_in_v1 = False
                for name1, _, _ in interfaces1:
                    if name == name1:
                        found_in_v1 = True
                        break
                
                if not found_in_v1:
                    # 新增的节点 - 绿色
                    dot.node(
                        name,
                        f"{name}\n({bus_type})\n{mode}",
                        shape="box",
                        style="filled",
                        fillcolor="#a6ffa6"
                    )

            # 添加连接
            # 1. 处理第一个版本中的连接
            for i, (name1, bus_type1, mode1) in enumerate(interfaces1):
                for j, (name2, bus_type2, mode2) in enumerate(interfaces1):
                    if i != j and mode1 == "master" and mode2 == "slave":
                        # 检查连接是否在第二个版本中存在
                        found_in_v2 = False
                        for k, (name3, bus_type3, mode3) in enumerate(interfaces2):
                            for l, (name4, bus_type4, mode4) in enumerate(interfaces2):
                                if k != l and name1 == name3 and name2 == name4 and mode3 == "master" and mode4 == "slave":
                                    found_in_v2 = True
                                    break
                            if found_in_v2:
                                break
                        
                        if found_in_v2:
                            # 未修改的连接 - 白色
                            dot.edge(name1, name2, color="#ffffff")
                        else:
                            # 删除的连接 - 红色
                            dot.edge(name1, name2, color="#ffa6a6")

            # 2. 处理第二个版本中的新连接
            for i, (name1, bus_type1, mode1) in enumerate(interfaces2):
                for j, (name2, bus_type2, mode2) in enumerate(interfaces2):
                    if i != j and mode1 == "master" and mode2 == "slave":
                        # 检查连接是否在第一个版本中存在
                        found_in_v1 = False
                        for k, (name3, bus_type3, mode3) in enumerate(interfaces1):
                            for l, (name4, bus_type4, mode4) in enumerate(interfaces1):
                                if k != l and name1 == name3 and name2 == name4 and mode3 == "master" and mode4 == "slave":
                                    found_in_v1 = True
                                    break
                            if found_in_v1:
                                break
                        
                        if not found_in_v1:
                            # 新增的连接 - 绿色
                            dot.edge(name1, name2, color="#a6ffa6")

            dot.format = "png"
            output_path = get_temp_filename("bus_intf_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"生成总线接口差异图时出错: {e}")
            return None

    def generate_ad_hoc_connections_diff_diagram(
        self, elements1, elements2, output_img="adhoc_conn_diff"
    ):
        """生成点对点连接差异图"""
        try:
            # 提取节点信息
            nodes1 = {item["name"]: item for item in elements1["adhocconnection"]}
            nodes2 = {item["name"]: item for item in elements2["adhocconnection"]}

            # 创建图
            dot = graphviz.Digraph(comment="Ad-hoc Connections Diff", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加节点
            for name in set(nodes1.keys()) | set(nodes2.keys()):
                if name in nodes1 and name in nodes2:
                    if nodes1[name] != nodes2[name]:
                        # 修改的节点
                        refs1 = nodes1[name].get("internalPortReferences", [])
                        refs2 = nodes2[name].get("internalPortReferences", [])
                        if len(refs1) >= 2 and len(refs2) >= 2:
                            label = f"{name}\n({refs1[0]['componentRef']}.{refs1[0]['portRef']} ↔ {refs1[1]['componentRef']}.{refs1[1]['portRef']})\n→\n({refs2[0]['componentRef']}.{refs2[0]['portRef']} ↔ {refs2[1]['componentRef']}.{refs2[1]['portRef']})"
                            dot.node(
                                name,
                                label,
                                shape="diamond",
                                style="filled",
                                fillcolor="orange",
                            )
                    else:
                        # 未修改的节点
                        refs = nodes1[name].get("internalPortReferences", [])
                        if len(refs) >= 2:
                            label = f"{name}\n({refs[0]['componentRef']}.{refs[0]['portRef']} ↔ {refs[1]['componentRef']}.{refs[1]['portRef']})"
                            dot.node(
                                name,
                                label,
                                shape="diamond",
                                style="filled",
                                fillcolor="lightgrey",
                            )
                elif name in nodes1:
                    # 删除的节点
                    refs = nodes1[name].get("internalPortReferences", [])
                    if len(refs) >= 2:
                        label = f"{name}\n({refs[0]['componentRef']}.{refs[0]['portRef']} ↔ {refs[1]['componentRef']}.{refs[1]['portRef']})"
                        dot.node(
                            name,
                            label,
                            shape="diamond",
                            style="filled",
                            fillcolor="red",
                        )
                else:
                    # 新增的节点
                    refs = nodes2[name].get("internalPortReferences", [])
                    if len(refs) >= 2:
                        label = f"{name}\n({refs[0]['componentRef']}.{refs[0]['portRef']} ↔ {refs[1]['componentRef']}.{refs[1]['portRef']})"
                        dot.node(
                            name,
                            label,
                            shape="diamond",
                            style="filled",
                            fillcolor="green",
                        )

            # 添加连接 - 按照连接名称的字母顺序连接
            sorted_nodes = sorted(set(nodes1.keys()) | set(nodes2.keys()))
            for i in range(len(sorted_nodes) - 1):
                # 检查两个节点是否在同一个版本中存在
                if (sorted_nodes[i] in nodes1 and sorted_nodes[i + 1] in nodes1) or (
                    sorted_nodes[i] in nodes2 and sorted_nodes[i + 1] in nodes2
                ):
                    dot.edge(sorted_nodes[i], sorted_nodes[i + 1])

            # 添加图例
            # dot.node('legend', 'Legend:\nGreen: Added\nRed: Removed\nOrange: Modified\nGrey: Unchanged',
            #         shape='box', style='filled', fillcolor='white')

            dot.format = "png"
            output_path = get_temp_filename("adhoc_conn_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"
            print(f"Generated ad-hoc connections diff diagram: {img_path}")

            # 转换为base64
            base64_str = image_to_base64(img_path)
            # 清理临时文件
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating ad-hoc connections diff diagram: {e}")
            return None

    def generate_memory_map_diff_diagram(
        self, elements1, elements2, output_img="memory_map_diff"
    ):
        """生成内存映射差异图"""
        try:
            # 提取内存映射信息
            mem_maps1 = {item["name"]: item for item in elements1["memorymap"]}
            mem_maps2 = {item["name"]: item for item in elements2["memorymap"]}

            dot = graphviz.Digraph(comment="Memory Map Diff", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加内存映射节点
            for name in set(mem_maps1.keys()) | set(mem_maps2.keys()):
                if name in mem_maps1 and name in mem_maps2:
                    if mem_maps1[name] != mem_maps2[name]:
                        # 修改的内存映射 - 使用#ffffa6
                        dot.node(
                            name, 
                            name, 
                            shape="box", 
                            style="filled", 
                            fillcolor="#ffffa6"
                        )
                    else:
                        # 未修改的内存映射 - 使用#ffffff
                        dot.node(
                            name,
                            name,
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff"
                        )
                elif name in mem_maps1:
                    # 删除的内存映射 - 使用#ffa6a6
                    dot.node(
                        name, 
                        name, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#ffa6a6"
                    )
                else:
                    # 新增的内存映射 - 使用#a6ffa6
                    dot.node(
                        name, 
                        name, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#a6ffa6"
                    )

                # 添加地址块节点
                if name in mem_maps1:
                    for block in mem_maps1[name].get("addressblocks", []):
                        block_name = f"{name}_{block['name']}"
                        # 检查在新版本中是否存在相同的地址块
                        block_in_v2 = None
                        if name in mem_maps2:
                            for b2 in mem_maps2[name].get("addressblocks", []):
                                if b2["name"] == block["name"]:
                                    block_in_v2 = b2
                                    break

                        if block_in_v2:
                            # 检查是否有变化
                            if (
                                block["baseAddress"] != block_in_v2["baseAddress"]
                                or block["range"] != block_in_v2["range"]
                                or block["width"] != block_in_v2["width"]
                            ):
                                # 修改的地址块 - 使用#ffffa6
                                label = f"{block['name']}\nBase: {block['baseAddress']} → {block_in_v2['baseAddress']}\nRange: {block['range']} → {block_in_v2['range']}\nWidth: {block['width']} → {block_in_v2['width']}"
                                dot.node(
                                    block_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffa6"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, block_name, color="#000000", style="solid")
                            else:
                                # 未修改的地址块 - 使用#ffffff
                                label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                                dot.node(
                                    block_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffff"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, block_name, color="#000000", style="solid")
                        else:
                            # 删除的地址块 - 使用#ffa6a6
                            label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                            dot.node(
                                block_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#ffa6a6"
                            )
                            # 删除的连接 - 使用#ffa6a6
                            dot.edge(name, block_name, color="#ffa6a6", style="solid")

                if name in mem_maps2:
                    for block in mem_maps2[name].get("addressblocks", []):
                        block_name = f"{name}_{block['name']}"
                        # 检查在旧版本中是否存在相同的地址块
                        block_in_v1 = None
                        if name in mem_maps1:
                            for b1 in mem_maps1[name].get("addressblocks", []):
                                if b1["name"] == block["name"]:
                                    block_in_v1 = b1
                                    break

                        if not block_in_v1:
                            # 新增的地址块 - 使用#a6ffa6
                            label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                            dot.node(
                                block_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#a6ffa6"
                            )
                            # 新增的连接 - 使用#a6ffa6
                            dot.edge(name, block_name, color="#a6ffa6", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("memory_map_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating memory map diff diagram: {e}")
            return None

    def generate_ipxact_diff_html(self, file1, file2, output_file):
        """生成IPXACT差异比较的HTML报告"""
        try:
            # 解析两个XML文件
            tree1 = ET.parse(file1)
            tree2 = ET.parse(file2)
            root1 = tree1.getroot()
            root2 = tree2.getroot()

            # 提取元素
            elements1 = self.extract_ipxact_elements(root1)
            elements2 = self.extract_ipxact_elements(root2)

            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            os.makedirs(output_dir, exist_ok=True)

            # 创建可视化器实例
            visualizer1 = IPXACTVisualizer(file1)
            visualizer2 = IPXACTVisualizer(file2)

            # 使用线程池并行生成图片
            max_workers = min(multiprocessing.cpu_count() * 2, 8)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有图片生成任务
                future_to_task = {
                    # 组件相关
                    executor.submit(
                        visualizer1.generate_component_diagram
                    ): "component1",
                    executor.submit(
                        visualizer2.generate_component_diagram
                    ): "component2",
                    executor.submit(
                        self.generate_component_diff_diagram, elements1, elements2
                    ): "component_diff",
                    executor.submit(
                        visualizer1.generate_component_instances_diagram
                    ): "componentinstance1",
                    executor.submit(
                        visualizer2.generate_component_instances_diagram
                    ): "componentinstance2",
                    executor.submit(
                        self.generate_component_instances_diff_diagram,
                        elements1,
                        elements2,
                    ): "componentinstance_diff",
                    # 总线相关
                    executor.submit(
                        visualizer1.generate_bus_definition_diagram
                    ): "busdefinition1",
                    executor.submit(
                        visualizer2.generate_bus_definition_diagram
                    ): "busdefinition2",
                    executor.submit(
                        self.generate_bus_definition_diff_diagram, elements1, elements2
                    ): "busdefinition_diff",
                    executor.submit(
                        visualizer1.generate_bus_interfaces_diagram
                    ): "businterface1",
                    executor.submit(
                        visualizer2.generate_bus_interfaces_diagram
                    ): "businterface2",
                    executor.submit(
                        self.generate_bus_interfaces_diff_diagram, elements1, elements2
                    ): "businterface_diff",
                    # 设计相关
                    executor.submit(visualizer1.generate_design_diagram): "design1",
                    executor.submit(visualizer2.generate_design_diagram): "design2",
                    executor.submit(
                        self.generate_design_diff_diagram, elements1, elements2
                    ): "design_diff",
                    # 视图相关
                    executor.submit(visualizer1.generate_view_diagram): "view1",
                    executor.submit(visualizer2.generate_view_diagram): "view2",
                    executor.submit(
                        self.generate_view_diff_diagram, elements1, elements2
                    ): "view_diff",
                    # 地址空间相关
                    executor.submit(
                        visualizer1.generate_address_space_diagram
                    ): "addressspace1",
                    executor.submit(
                        visualizer2.generate_address_space_diagram
                    ): "addressspace2",
                    executor.submit(
                        self.generate_address_space_diff_diagram, elements1, elements2
                    ): "addressspace_diff",
                    # 寄存器相关
                    executor.submit(visualizer1.generate_register_diagram): "register1",
                    executor.submit(visualizer2.generate_register_diagram): "register2",
                    executor.submit(
                        self.generate_register_diff_diagram, elements1, elements2
                    ): "register_diff",
                    # 内存映射相关
                    executor.submit(
                        visualizer1.generate_memory_map_diagram
                    ): "memorymap1",
                    executor.submit(
                        visualizer2.generate_memory_map_diagram
                    ): "memorymap2",
                    executor.submit(
                        self.generate_memory_map_diff_diagram, elements1, elements2
                    ): "memorymap_diff",
                }

                # 收集结果
                results = {}
                for future in as_completed(future_to_task):
                    task_name = future_to_task[future]
                    try:
                        results[task_name] = future.result()
                    except Exception as e:
                        print(f"Error generating {task_name}: {e}")
                        results[task_name] = None

            # 生成HTML内容
            base_name1 = os.path.splitext(os.path.basename(file1))[0]
            base_name2 = os.path.splitext(os.path.basename(file2))[0]
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>IPXACT Diff Report: {base_name1} vs {base_name2}</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/style.min.css" />
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/jstree.min.js"></script>
                <style>
                    body {{ font-family: Consolas, monospace; margin: 20px; }}
                    .section {{ margin: 20px 0; }}
                    .section-title {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f5f5f5; }}
                    .added {{ background-color: #e6ffe6; }}
                    .removed {{ background-color: #ffe6e6; }}
                    .modified {{ background-color: #ffffe6; }}
                    .summary {{ margin: 20px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }}
                    .summary-item {{ margin: 5px 0; }}
                    .image-comparison {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                    .image-container {{ width: 48%; }}
                    .image-container img {{ width: 100%; max-width: 600px; height: auto; }}
                    .image-label {{ text-align: center; margin: 5px 0; }}
                    .content-section {{ margin: 20px; }}
                    .diagram-section {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
                    .header {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>IPXACT Diff Report</h1>
                    <p>Comparing {base_name1} vs {base_name2}</p>
                    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            """

            # 添加内容区域
            html_content += '<div class="content-section">'

            # 生成差异统计
            stats = defaultdict(lambda: {"added": 0, "removed": 0, "modified": 0})
            for section in elements1.keys():
                items1 = {item["name"]: item for item in elements1[section]}
                items2 = {item["name"]: item for item in elements2[section]}
                all_keys = set(items1.keys()) | set(items2.keys())

                for key in all_keys:
                    if key in items1 and key in items2:
                        if items1[key] != items2[key]:
                            stats[section]["modified"] += 1
                    elif key in items1:
                        stats[section]["removed"] += 1
                    else:
                        stats[section]["added"] += 1

            # 显示统计摘要
            html_content += '<div class="section" id="summary">'
            html_content += "<h2>Summary of Changes</h2>"
            for section, counts in stats.items():
                if sum(counts.values()) > 0:
                    html_content += f'<div class="summary-item">'
                    html_content += f"<strong>{section}:</strong> "
                    changes = []
                    if counts["added"] > 0:
                        changes.append(f"{counts['added']} added")
                    if counts["removed"] > 0:
                        changes.append(f"{counts['removed']} removed")
                    if counts["modified"] > 0:
                        changes.append(f"{counts['modified']} modified")
                    html_content += ", ".join(changes)
                    html_content += "</div>"
            html_content += "</div>"

            # 为每个部分生成内容
            sections = [
                "component",
                "componentinstance",
                "busdefinition",
                "businterface",
                "design",
                "view",
                "addressspace",
                "memorymap",
                "register",
            ]
            for section in sections:
                html_content += f'<div class="section" id="{section}">'
                html_content += f'<div class="section-title">{section.title()}</div>'

                # 生成差异表格
                html_content += self._generate_diff_table(section, elements1, elements2)

                # 添加对应的图片
                if (
                    section == "component"
                    and results.get("component1")
                    and results.get("component2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += '<div class="section-title">Component Diagram</div>'
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["component1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["component2"]}"></div>'
                    html_content += "</div>"
                    if results.get("component_diff"):
                        html_content += (
                            '<div class="section-title">Component Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["component_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "componentinstance"
                    and results.get("componentinstance1")
                    and results.get("componentinstance2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += (
                        '<div class="section-title">Component Instance Diagram</div>'
                    )
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["componentinstance1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["componentinstance2"]}"></div>'
                    html_content += "</div>"
                    if results.get("componentinstance_diff"):
                        html_content += '<div class="section-title">Component Instance Differences</div>'
                        html_content += f'<div class="image-container"><img src="{results["componentinstance_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "busdefinition"
                    and results.get("busdefinition1")
                    and results.get("busdefinition2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += (
                        '<div class="section-title">Bus Definition Diagram</div>'
                    )
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["busdefinition1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["busdefinition2"]}"></div>'
                    html_content += "</div>"
                    if results.get("busdefinition_diff"):
                        html_content += '<div class="section-title">Bus Definition Differences</div>'
                        html_content += f'<div class="image-container"><img src="{results["busdefinition_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "businterface"
                    and results.get("businterface1")
                    and results.get("businterface2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += (
                        '<div class="section-title">Bus Interface Diagram</div>'
                    )
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["businterface1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["businterface2"]}"></div>'
                    html_content += "</div>"
                    if results.get("businterface_diff"):
                        html_content += (
                            '<div class="section-title">Bus Interface Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["businterface_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "design"
                    and results.get("design1")
                    and results.get("design2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += '<div class="section-title">Design Diagram</div>'
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["design1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["design2"]}"></div>'
                    html_content += "</div>"
                    if results.get("design_diff"):
                        html_content += (
                            '<div class="section-title">Design Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["design_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "view" and results.get("view1") and results.get("view2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += '<div class="section-title">View Diagram</div>'
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["view1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["view2"]}"></div>'
                    html_content += "</div>"
                    if results.get("view_diff"):
                        html_content += (
                            '<div class="section-title">View Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["view_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "addressspace"
                    and results.get("addressspace1")
                    and results.get("addressspace2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += (
                        '<div class="section-title">Address Space Diagram</div>'
                    )
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["addressspace1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["addressspace2"]}"></div>'
                    html_content += "</div>"
                    if results.get("addressspace_diff"):
                        html_content += (
                            '<div class="section-title">Address Space Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["addressspace_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "register"
                    and results.get("register1")
                    and results.get("register2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += '<div class="section-title">Register Diagram</div>'
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["register1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["register2"]}"></div>'
                    html_content += "</div>"
                    if results.get("register_diff"):
                        html_content += (
                            '<div class="section-title">Register Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["register_diff"]}"></div>'
                    html_content += "</div>"

                elif (
                    section == "memorymap"
                    and results.get("memorymap1")
                    and results.get("memorymap2")
                ):
                    html_content += '<div class="diagram-section">'
                    html_content += (
                        '<div class="section-title">Memory Map Diagram</div>'
                    )
                    html_content += '<div class="image-comparison">'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name1}</div><img src="{results["memorymap1"]}"></div>'
                    html_content += f'<div class="image-container"><div class="image-label">{base_name2}</div><img src="{results["memorymap2"]}"></div>'
                    html_content += "</div>"
                    if results.get("memorymap_diff"):
                        html_content += (
                            '<div class="section-title">Memory Map Differences</div>'
                        )
                        html_content += f'<div class="image-container"><img src="{results["memorymap_diff"]}"></div>'
                    html_content += "</div>"

                html_content += "</div>"

            html_content += "</div></body></html>"

            # 写入HTML文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"IPXACT比较报告已生成: {output_file}")
            return True

        except Exception as e:
            print(f"生成IPXACT比较报告时出错: {str(e)}")
            return False

    def generate_component_instances_diagram(self, output_img="component_instances"):
        """生成组件实例图"""
        try:
            # 提取组件实例
            components = []
            for ci in self.root.findall(".//spirit:componentInstance", self.ns):
                name = ci.findtext("spirit:name", default="N/A", namespaces=self.ns)
                type_elem = ci.find("spirit:componentRef", self.ns)
                type_name = (
                    type_elem.get(
                        "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014}name"
                    )
                    if type_elem is not None
                    else "N/A"
                )
                components.append((name, type_name))

            if not components:
                return None

            dot = graphviz.Digraph(comment="Component Instances", engine="dot")
            dot.attr(rankdir="TB", dpi="300")
            # 添加组件节点
            for name, type_name in components:
                dot.node(
                    name,
                    f"{name}\n({type_name})",
                    shape="box",
                    style="filled",
                    fillcolor="#ffffff",
                )

            # 查找ad-hoc连接，收集唯一连接对
            connections = set()
            for conn in self.root.findall(".//spirit:adHocConnection", self.ns):
                refs = conn.findall("spirit:internalPortReference", self.ns)
                if len(refs) >= 2:
                    comp1 = refs[0].get(
                        "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014}componentRef"
                    )
                    comp2 = refs[1].get(
                        "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014}componentRef"
                    )
                    if comp1 and comp2:
                        connections.add((comp1, comp2))
            # 添加连接线
            for comp1, comp2 in connections:
                dot.edge(comp1, comp2, color="#000000", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("component_instances", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"
            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating component instances diagram: {e}")
            return None


    def generate_bus_interfaces_diagram(self, output_img="bus_interfaces"):
        """生成总线接口图"""
        try:
            # 使用与extract_ipxact_elements相同的逻辑提取总线接口
            interfaces = []
            for intf in self.root.findall(".//spirit:busInterface", self.ns):
                name = intf.findtext("spirit:name", default="N/A", namespaces=self.ns)
                bus_type = intf.find("spirit:busType", self.ns)
                bus_type_name = (
                    bus_type.get(f"{{{self.ns['spirit']}}}name") if bus_type is not None else "N/A"
                )
                mode = (
                    "master"
                    if intf.find("spirit:master", self.ns) is not None
                    else "slave"
                )
                interfaces.append((name, bus_type_name, mode))

            if not interfaces:
                return None

            dot = graphviz.Digraph(comment="Bus Interfaces", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")  # 设置白色背景

            # 添加接口节点
            for name, bus_type, mode in interfaces:
                dot.node(
                    name,
                    f"{name}\n({bus_type})\n{mode}",
                    shape="box",
                    style="filled",
                    fillcolor="white",  # 使用白色背景
                )

            # 添加连接
            # 只建立从master到slave的单向连接
            for i, (name1, bus_type1, mode1) in enumerate(interfaces):
                for j, (name2, bus_type2, mode2) in enumerate(interfaces):
                    if i != j:  # 避免自连接
                        # 只建立从master到slave的连接
                        if mode1 == "master" and mode2 == "slave":
                            dot.edge(name1, name2, color="#000000")

            dot.format = "png"
            # 使用临时文件名
            output_path = get_temp_filename("bus_interfaces", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            # 转换为base64
            base64_str = image_to_base64(img_path)
            # 清理临时文件
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"生成总线接口图时出错: {e}")
            return None

    def generate_ad_hoc_connections_diagram(self, elements=None):
        """生成Ad-hoc连接关系图"""
        if elements is None:
            # 如果没有传入elements，从当前XML文件中提取
            elements = self.extract_ipxact_elements(self.root)

        dot = graphviz.Digraph("Ad-hoc Connections", format="png")
        dot.attr(rankdir="LR")

        # 提取所有Ad-hoc连接
        connections = []
        for element in elements.get("adhocconnection", []):
            name = element.get("name", "")
            # 提取组件引用和端口引用
            comp_refs = []
            port_refs = []
            for ref in element.get("internalPortReferences", []):
                comp_ref = ref.get("componentRef", "")
                port_ref = ref.get("portRef", "")
                if comp_ref and port_ref:
                    comp_refs.append(comp_ref)
                    port_refs.append(port_ref)
            if len(comp_refs) == 2:
                connections.append(
                    (name, comp_refs[0], comp_refs[1], port_refs[0], port_refs[1])
                )

        # 添加节点和边
        for name, comp1, comp2, port1, port2 in connections:
            # 创建节点标签，包含端口信息
            label1 = f"{comp1}\n({port1})"
            label2 = f"{comp2}\n({port2})"

            # 添加节点
            dot.node(comp1, label1, shape="box", style="filled", fillcolor="lightblue")
            dot.node(comp2, label2, shape="box", style="filled", fillcolor="lightblue")

            # 添加边
            dot.edge(comp1, comp2, label=name, style="solid", color="black")

        # 添加图例
        # dot.node('legend', 'Ad-hoc Connections\n(Component Name)\n(Port Name)',
        #         shape='box', style='filled', fillcolor='lightblue')

        # 渲染图
        output_path = get_temp_filename("ad_hoc_connections", "")
        dot.render(output_path, cleanup=True)
        img_path = output_path + ".png"

        # 将图转换为base64字符串
        base64_str = image_to_base64(img_path)
        if os.path.exists(img_path):
            os.remove(img_path)
        return base64_str

    def generate_memory_map_diagram(self, output_img="memory_map"):
        """生成内存映射图"""
        try:
            # 提取内存映射信息
            memory_maps = []
            for mm in self.root.findall(".//spirit:memoryMap", self.ns):
                mm_name = mm.findtext("spirit:name", default="N/A", namespaces=self.ns)
                mm_data = {"name": mm_name, "addressblocks": []}
                for ab in mm.findall(".//spirit:addressBlock", self.ns):
                    ab_data = {
                        "name": ab.findtext(
                            "spirit:name", default="N/A", namespaces=self.ns
                        ),
                        "baseAddress": ab.findtext(
                            "spirit:baseAddress", default="N/A", namespaces=self.ns
                        ),
                        "range": ab.findtext(
                            "spirit:range", default="N/A", namespaces=self.ns
                        ),
                        "width": ab.findtext(
                            "spirit:width", default="N/A", namespaces=self.ns
                        ),
                    }
                    mm_data["addressblocks"].append(ab_data)
                memory_maps.append(mm_data)

            if not memory_maps:
                print("No memory maps found")
                return None

            dot = graphviz.Digraph(comment="Memory Map", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加内存映射节点
            for mm in memory_maps:
                mm_name = mm["name"]
                dot.node(
                    mm_name, 
                    mm_name, 
                    shape="box", 
                    style="filled", 
                    fillcolor="#ffffff"
                )

                # 添加地址块节点
                for ab in mm["addressblocks"]:
                    ab_name = f"{mm_name}_{ab['name']}"
                    label = f"{ab['name']}\nBase: {ab['baseAddress']}\nRange: {ab['range']}\nWidth: {ab['width']}"
                    dot.node(
                        ab_name,
                        label,
                        shape="box",
                        style="filled",
                        fillcolor="#ffffff"
                    )
                    # 添加黑色实线连接
                    dot.edge(mm_name, ab_name, color="#000000", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("memory_map", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating memory map diagram: {e}")
            return None

    def _generate_component_diagram(self, elements1, elements2):
        """生成组件和实例关系图"""
        diagram = []

        # 添加组件节点
        comp1 = elements1.get("component", [{}])[0]
        comp2 = elements2.get("component", [{}])[0]
        comp_name = comp1.get("name", "N/A")
        status = self._get_element_status(comp1, comp2)

        diagram.append(f'    {comp_name}["{comp_name}"]')

        # 添加实例节点，保持原始顺序
        instances = []
        for inst in elements1.get("componentinstance", []):
            inst_name = inst.get("name", "N/A")
            instances.append(inst_name)
            diagram.append(f'    {inst_name}["{inst_name}"]')

        # 按照原始顺序添加连接关系
        for inst_name in instances:
            diagram.append(f"    {comp_name} --> {inst_name}")

        return "\n".join(diagram)

    def generate_component_diagram(self, output_img="component"):
        """生成组件图"""
        try:
            # 提取组件信息
            component = self.root.find(".//spirit:component", self.ns)
            if component is None:
                print("No component found")
                return None

            name = component.findtext("spirit:name", default="N/A", namespaces=self.ns)
            version = component.findtext(
                "spirit:version", default="N/A", namespaces=self.ns
            )
            vendor = component.findtext(
                "spirit:vendor", default="N/A", namespaces=self.ns
            )

            # 提取总线接口
            bus_interfaces = []
            for bus_if in component.findall(".//spirit:busInterface", self.ns):
                bus_name = bus_if.findtext(
                    "spirit:name", default="N/A", namespaces=self.ns
                )
                bus_type = bus_if.findtext(
                    ".//spirit:name", default="N/A", namespaces=self.ns
                )
                bus_interfaces.append((bus_name, bus_type))

            # 提取端口
            ports = []
            for port in component.findall(".//spirit:port", self.ns):
                port_name = port.findtext(
                    "spirit:name", default="N/A", namespaces=self.ns
                )
                port_type = port.findtext(
                    ".//spirit:wire/spirit:direction", default="N/A", namespaces=self.ns
                )
                ports.append((port_name, port_type))

            dot = graphviz.Digraph(comment="Component", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加组件节点
            component_label = f"{name}\nVersion: {version}\nVendor: {vendor}"
            dot.node(
                name,
                component_label,
                shape="box",
                style="filled",
                fillcolor="lightblue",
            )

            # 添加总线接口节点
            for bus_name, bus_type in bus_interfaces:
                bus_label = f"{bus_name}\n({bus_type})"
                dot.node(
                    bus_name,
                    bus_label,
                    shape="box",
                    style="filled",
                    fillcolor="lightyellow",
                )
                dot.edge(name, bus_name)

            # 添加端口节点
            for port_name, port_type in ports:
                port_label = f"{port_name}\n({port_type})"
                dot.node(
                    port_name,
                    port_label,
                    shape="box",
                    style="filled",
                    fillcolor="lightgreen",
                )
                dot.edge(name, port_name)

            dot.format = "png"
            output_path = get_temp_filename("component", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating component diagram: {e}")
            return None

    def generate_bus_definition_diagram(self, output_img="bus_definition"):
        """生成总线定义图"""
        try:
            # 提取总线定义
            bus_defs = []
            for bus in self.root.findall(".//spirit:busDefinition", self.ns):
                name = bus.findtext("spirit:name", default="N/A", namespaces=self.ns)
                version = bus.findtext(
                    "spirit:version", default="N/A", namespaces=self.ns
                )
                bus_defs.append((name, version))

            if not bus_defs:
                return None

            # 提取总线接口信息
            bus_interfaces = []
            for intf in self.root.findall(".//spirit:busInterface", self.ns):
                bus_type = intf.find("spirit:busType", self.ns)
                if bus_type is not None:
                    bus_name = bus_type.get("spirit:name")
                    if bus_name:  # 确保bus_name不为None
                        # 检查是否是主设备
                        is_master = intf.find("spirit:master", self.ns) is not None
                        intf_name = intf.findtext(
                            "spirit:name", default="N/A", namespaces=self.ns
                        )
                        bus_interfaces.append((intf_name, bus_name, is_master))

            # 创建图
            dot = graphviz.Digraph(comment="Bus Definitions", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加总线定义节点
            for name, version in bus_defs:
                dot.node(
                    name,
                    f"{name}\nVersion: {version}",
                    shape="box",
                    style="filled",
                    fillcolor="#ffffff",
                )

            # 添加一个测试连接
            if len(bus_defs) >= 2:
                dot.edge(bus_defs[0][0], bus_defs[1][0], color="#000000", style="solid")

            # 生成图片
            dot.format = "png"
            output_path = get_temp_filename("bus_definition", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating bus definition diagram: {e}")
            return None

    def generate_design_diagram(self, output_img="design"):
        """生成设计实例图"""
        try:
            # 提取设计信息
            design = self.root.find(".//spirit:design", self.ns)
            if design is None:
                print("No design found")
                return None

            # 获取设计名称和版本
            design_name = design.findtext(
                "spirit:name", default="N/A", namespaces=self.ns
            )
            design_version = design.findtext(
                "spirit:version", default="N/A", namespaces=self.ns
            )

            # 提取组件实例
            instances = []
            for ci in design.findall(".//spirit:componentInstance", self.ns):
                name = ci.findtext("spirit:name", default="N/A", namespaces=self.ns)
                type_elem = ci.find("spirit:componentRef", self.ns)
                type_name = (
                    type_elem.get(f"{{{self.ns['spirit']}}}name") if type_elem is not None else "N/A"
                )
                instances.append((name, type_name))

            # 提取连接关系
            connections = []
            # 处理总线连接
            for conn in design.findall(".//spirit:interconnection", self.ns):
                active = conn.findtext(
                    "spirit:activeInterface", default="N/A", namespaces=self.ns
                )
                hier = conn.findtext(
                    "spirit:hierInterface", default="N/A", namespaces=self.ns
                )
                if active != "N/A" and hier != "N/A":
                    connections.append((active, hier, "bus"))

            # 处理点对点连接
            for conn in design.findall(".//spirit:adHocConnection", self.ns):
                refs = conn.findall("spirit:internalPortReference", self.ns)
                if len(refs) >= 2:
                    comp1 = refs[0].get(f"{{{self.ns['spirit']}}}componentRef", "N/A")
                    comp2 = refs[1].get(f"{{{self.ns['spirit']}}}componentRef", "N/A")
                    if comp1 != "N/A" and comp2 != "N/A":
                        connections.append((comp1, comp2, "ad-hoc"))

            dot = graphviz.Digraph(comment="Design", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加设计节点
            dot.node(
                design_name,
                f"{design_name}\nVersion: {design_version}",
                shape="box",
                style="filled",
                fillcolor="white"
            )

            # 添加组件实例节点
            for name, type_name in instances:
                if type_name != "N/A":
                    dot.node(
                        name,
                        f"{name}\n({type_name})",
                        shape="box",
                        style="filled",
                        fillcolor="white"
                    )

            # 添加design到instance的连线
            for name, _ in instances:
                dot.edge(design_name, name, style="solid", color="black")

            # 添加连接关系
            for comp1, comp2, conn_type in connections:
                if conn_type == "bus":
                    dot.edge(comp1, comp2, label="bus", style="solid", color="black")
                else:  # ad-hoc
                    dot.edge(comp1, comp2, label="ad-hoc", style="solid", color="black")

            dot.format = "png"
            output_path = get_temp_filename("design", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating design diagram: {e}")
            return None

    def generate_view_diagram(self, output_img="view"):
        """生成视图图"""
        try:
            # 提取视图信息
            views = []
            for view in self.root.findall(".//spirit:view", self.ns):
                name = view.findtext("spirit:name", default="N/A", namespaces=self.ns)
                env = view.findtext(
                    "spirit:envIdentifier", default="N/A", namespaces=self.ns
                )
                views.append((name, env))

            if not views:
                print("No views found")
                return None

            dot = graphviz.Digraph(comment="Views", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加视图节点
            for name, env in views:
                dot.node(
                    name,
                    f"{name}\n({env})",
                    shape="box",
                    style="filled",
                    fillcolor="white",
                )

            # 添加视图之间的连接
            for i in range(len(views) - 1):
                dot.edge(views[i][0], views[i + 1][0], color="black", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("view", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating view diagram: {e}")
            return None

    def generate_address_space_diagram(self, output_img="address_space"):
        """生成地址空间图"""
        try:
            # 提取地址空间信息
            addr_spaces = []
            for space in self.root.findall(".//spirit:addressSpace", self.ns):
                name = space.findtext("spirit:name", default="N/A", namespaces=self.ns)
                range_elem = space.find("spirit:range", self.ns)
                range_val = range_elem.text if range_elem is not None else "N/A"
                width_elem = space.find("spirit:width", self.ns)
                width_val = width_elem.text if width_elem is not None else "N/A"
                addr_spaces.append((name, range_val, width_val))

            if not addr_spaces:
                print("No address spaces found")
                return None

            dot = graphviz.Digraph(comment="Address Spaces", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加地址空间节点
            for name, range_val, width_val in addr_spaces:
                label = f"{name}\nRange: {range_val}\nWidth: {width_val}"
                dot.node(
                    name, 
                    label, 
                    shape="box", 
                    style="filled", 
                    fillcolor="#ffffff"
                )

            # 添加连接线
            for i in range(len(addr_spaces) - 1):
                dot.edge(addr_spaces[i][0], addr_spaces[i + 1][0], color="#000000", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("address_space", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating address space diagram: {e}")
            return None

    def generate_register_diagram(self, output_img="register"):
        """生成寄存器图"""
        try:
            # 提取寄存器信息
            registers = []
            for reg in self.root.findall(".//spirit:register", self.ns):
                name = reg.findtext("spirit:name", default="N/A", namespaces=self.ns)
                offset = reg.findtext(
                    "spirit:addressOffset", default="N/A", namespaces=self.ns
                )
                size = reg.findtext("spirit:size", default="N/A", namespaces=self.ns)
                access = reg.findtext(
                    "spirit:access", default="N/A", namespaces=self.ns
                )

                # 提取字段信息
                fields = []
                for field in reg.findall(".//spirit:field", self.ns):
                    field_name = field.findtext(
                        "spirit:name", default="N/A", namespaces=self.ns
                    )
                    bit_offset = field.findtext(
                        "spirit:bitOffset", default="N/A", namespaces=self.ns
                    )
                    bit_width = field.findtext(
                        "spirit:bitWidth", default="N/A", namespaces=self.ns
                    )
                    field_access = field.findtext(
                        "spirit:access", default="N/A", namespaces=self.ns
                    )
                    fields.append((field_name, bit_offset, bit_width, field_access))

                registers.append((name, offset, size, access, fields))

            if not registers:
                print("No registers found")
                return None

            dot = graphviz.Digraph(comment="Registers", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加寄存器节点
            for name, offset, size, access, fields in registers:
                # 创建寄存器节点
                reg_label = f"{name}\nOffset: {offset}\nSize: {size}\nAccess: {access}"
                dot.node(
                    name, 
                    reg_label, 
                    shape="box", 
                    style="filled", 
                    fillcolor="#ffffff"
                )

                # 添加字段节点
                for field_name, bit_offset, bit_width, field_access in fields:
                    field_label = f"{field_name}\nBits: {bit_offset}:{int(bit_offset) + int(bit_width) - 1}\nAccess: {field_access}"
                    field_id = f"{name}_{field_name}"
                    dot.node(
                        field_id,
                        field_label,
                        shape="box",
                        style="filled",
                        fillcolor="#ffffff"
                    )
                    # 添加黑色实线连接
                    dot.edge(name, field_id, color="#000000", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("register", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating register diagram: {e}")
            return None

    def generate_design_diff_diagram(self, elements1, elements2, output_img="design_diff"):
        """生成设计差异图"""
        try:
            # 提取设计信息
            design1 = elements1.get("design", [{}])[0]
            design2 = elements2.get("design", [{}])[0]

            # 创建图
            dot = graphviz.Digraph(comment="Design Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 提取组件实例
            instances1 = {}
            for inst in design1.get("componentinstances", []):
                name = inst.get("name", "N/A")
                type_elem = inst.get("componentRef", "N/A")
                instances1[name] = {"name": name, "componentRef": type_elem}

            instances2 = {}
            for inst in design2.get("componentinstances", []):
                name = inst.get("name", "N/A")
                type_elem = inst.get("componentRef", "N/A")
                instances2[name] = {"name": name, "componentRef": type_elem}

            # 添加设计节点
            if design1 and design2:
                if design1 != design2:
                    # 修改的节点
                    label = f"{design1.get('name', 'N/A')}\nVersion: {design1.get('version', 'N/A')} → {design2.get('version', 'N/A')}"
                    dot.node(
                        "design", label, shape="box", style="filled", fillcolor="#ffffa6"
                    )
                else:
                    # 未修改的节点
                    label = f"{design1.get('name', 'N/A')}\nVersion: {design1.get('version', 'N/A')}"
                    dot.node(
                        "design",
                        label,
                        shape="box",
                        style="filled",
                        fillcolor="#ffffff"
                    )
            elif design1:
                # 删除的节点
                label = f"{design1.get('name', 'N/A')}\nVersion: {design1.get('version', 'N/A')}"
                dot.node("design", label, shape="box", style="filled", fillcolor="#ffa6a6")
            elif design2:
                # 新增的节点
                label = f"{design2.get('name', 'N/A')}\nVersion: {design2.get('version', 'N/A')}"
                dot.node(
                    "design", label, shape="box", style="filled", fillcolor="#a6ffa6"
                )

            # 添加组件实例节点
            for name in set(instances1.keys()) | set(instances2.keys()):
                if name in instances1 and name in instances2:
                    if instances1[name] != instances2[name]:
                        # 修改的节点
                        comp_ref1 = instances1[name].get('componentRef', 'N/A')
                        comp_ref2 = instances2[name].get('componentRef', 'N/A')
                        dot.node(
                            name,
                            f"{name}\n({comp_ref1} → {comp_ref2})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffa6"
                        )
                    else:
                        # 未修改的节点
                        comp_ref = instances1[name].get('componentRef', 'N/A')
                        dot.node(
                            name,
                            f"{name}\n({comp_ref})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff"
                        )
                elif name in instances1:
                    # 删除的节点
                    comp_ref = instances1[name].get('componentRef', 'N/A')
                    dot.node(
                        name,
                        f"{name}\n({comp_ref})",
                        shape="box",
                        style="filled",
                        fillcolor="#ffa6a6"
                    )
                else:
                    # 新增的节点
                    comp_ref = instances2[name].get('componentRef', 'N/A')
                    dot.node(
                        name,
                        f"{name}\n({comp_ref})",
                        shape="box",
                        style="filled",
                        fillcolor="#a6ffa6"
                    )

                # 添加与设计的连接
                if name in instances1 and name in instances2:
                    # 未修改的连接
                    dot.edge("design", name, color="black")
                elif name in instances1:
                    # 删除的连接
                    dot.edge("design", name, color="#ffa6a6")
                else:
                    # 新增的连接
                    dot.edge("design", name, color="#a6ffa6")

            dot.format = "png"
            output_path = get_temp_filename("design_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating design diff diagram: {e}")
            return None

    def generate_view_diff_diagram(self, elements1, elements2, output_img="view_diff"):
        """生成视图差异图"""
        try:
            # 提取视图信息
            views1 = {item["name"]: item for item in elements1.get("view", [])}
            views2 = {item["name"]: item for item in elements2.get("view", [])}

            # 创建图
            dot = graphviz.Digraph(comment="View Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加视图节点
            for name in set(views1.keys()) | set(views2.keys()):
                if name in views1 and name in views2:
                    if views1[name] != views2[name]:
                        # 修改的节点 - 使用#ffffa6
                        dot.node(
                            name,
                            f"{name}\n({views1[name].get('envIdentifier', 'N/A')} → {views2[name].get('envIdentifier', 'N/A')})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffa6"
                        )
                    else:
                        # 未修改的节点 - 使用#ffffff
                        dot.node(
                            name,
                            f"{name}\n({views1[name].get('envIdentifier', 'N/A')})",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff"
                        )
                elif name in views1:
                    # 删除的节点 - 使用#ffa6a6
                    dot.node(
                        name,
                        f"{name}\n({views1[name].get('envIdentifier', 'N/A')})",
                        shape="box",
                        style="filled",
                        fillcolor="#ffa6a6"
                    )
                else:
                    # 新增的节点 - 使用#a6ffa6
                    dot.node(
                        name,
                        f"{name}\n({views2[name].get('envIdentifier', 'N/A')})",
                        shape="box",
                        style="filled",
                        fillcolor="#a6ffa6"
                    )

            # 添加连接 - 按照视图名称的字母顺序连接
            sorted_nodes = sorted(set(views1.keys()) | set(views2.keys()))
            for i in range(len(sorted_nodes) - 1):
                node1 = sorted_nodes[i]
                node2 = sorted_nodes[i + 1]
                
                # 检查两个节点是否在同一个版本中存在
                if node1 in views1 and node2 in views1:
                    if node1 in views2 and node2 in views2:
                        # 两个版本中都存在的连接 - 使用#000000
                        dot.edge(node1, node2, color="#000000")
                    else:
                        # 只在第一个版本中存在的连接 - 使用#ffa6a6
                        dot.edge(node1, node2, color="#ffa6a6")
                elif node1 in views2 and node2 in views2:
                    # 只在第二个版本中存在的连接 - 使用#a6ffa6
                    dot.edge(node1, node2, color="#a6ffa6")

            dot.format = "png"
            output_path = get_temp_filename("view_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating view diff diagram: {e}")
            return None

    def generate_address_space_diff_diagram(
        self, elements1, elements2, output_img="address_space_diff"
    ):
        """生成地址空间差异图"""
        try:
            # 提取地址空间信息
            spaces1 = {item["name"]: item for item in elements1.get("addressspace", [])}
            spaces2 = {item["name"]: item for item in elements2.get("addressspace", [])}

            # 创建图
            dot = graphviz.Digraph(comment="Address Space Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加地址空间节点
            for name in set(spaces1.keys()) | set(spaces2.keys()):
                if name in spaces1 and name in spaces2:
                    if spaces1[name] != spaces2[name]:
                        # 修改的节点 - 使用#ffffa6
                        label = f"{name}\nRange: {spaces1[name].get('range', 'N/A')} → {spaces2[name].get('range', 'N/A')}\nWidth: {spaces1[name].get('width', 'N/A')} → {spaces2[name].get('width', 'N/A')}"
                        dot.node(
                            name, 
                            label, 
                            shape="box", 
                            style="filled", 
                            fillcolor="#ffffa6"
                        )
                    else:
                        # 未修改的节点 - 使用#ffffff
                        label = f"{name}\nRange: {spaces1[name].get('range', 'N/A')}\nWidth: {spaces1[name].get('width', 'N/A')}"
                        dot.node(
                            name,
                            label,
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff"
                        )
                elif name in spaces1:
                    # 删除的节点 - 使用#ffa6a6
                    label = f"{name}\nRange: {spaces1[name].get('range', 'N/A')}\nWidth: {spaces1[name].get('width', 'N/A')}"
                    dot.node(
                        name, 
                        label, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#ffa6a6"
                    )
                else:
                    # 新增的节点 - 使用#a6ffa6
                    label = f"{name}\nRange: {spaces2[name].get('range', 'N/A')}\nWidth: {spaces2[name].get('width', 'N/A')}"
                    dot.node(
                        name, 
                        label, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#a6ffa6"
                    )

                # 添加地址块节点
                if name in spaces1:
                    for block in spaces1[name].get("addressblocks", []):
                        block_name = f"{name}_{block['name']}"
                        # 检查在新版本中是否存在相同的地址块
                        block_in_v2 = None
                        if name in spaces2:
                            for b2 in spaces2[name].get("addressblocks", []):
                                if b2["name"] == block["name"]:
                                    block_in_v2 = b2
                                    break

                        if block_in_v2:
                            # 检查是否有变化
                            if (
                                block["baseAddress"] != block_in_v2["baseAddress"]
                                or block["range"] != block_in_v2["range"]
                            ):
                                # 修改的地址块 - 使用#ffffa6
                                label = f"{block['name']}\nBase: {block['baseAddress']} → {block_in_v2['baseAddress']}\nRange: {block['range']} → {block_in_v2['range']}\nWidth: {block['width']} → {block_in_v2['width']}"
                                dot.node(
                                    block_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffa6"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, block_name, color="#000000", style="solid")
                            else:
                                # 未修改的地址块 - 使用#ffffff
                                label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                                dot.node(
                                    block_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffff"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, block_name, color="#000000", style="solid")
                        else:
                            # 删除的地址块 - 使用#ffa6a6
                            label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                            dot.node(
                                block_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#ffa6a6"
                            )
                            # 删除的连接 - 使用#ffa6a6
                            dot.edge(name, block_name, color="#ffa6a6", style="solid")

                if name in spaces2:
                    for block in spaces2[name].get("addressblocks", []):
                        block_name = f"{name}_{block['name']}"
                        # 检查在旧版本中是否存在相同的地址块
                        block_in_v1 = None
                        if name in spaces1:
                            for b1 in spaces1[name].get("addressblocks", []):
                                if b1["name"] == block["name"]:
                                    block_in_v1 = b1
                                    break

                        if not block_in_v1:
                            # 新增的地址块 - 使用#a6ffa6
                            label = f"{block['name']}\nBase: {block['baseAddress']}\nRange: {block['range']}\nWidth: {block['width']}"
                            dot.node(
                                block_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#a6ffa6"
                            )
                            # 新增的连接 - 使用#a6ffa6
                            dot.edge(name, block_name, color="#a6ffa6", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("address_space_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating address space diff diagram: {e}")
            return None

    def generate_register_diff_diagram(
        self, elements1, elements2, output_img="register_diff"
    ):
        """生成寄存器差异图"""
        try:
            # 提取寄存器信息
            registers1 = {item["name"]: item for item in elements1.get("register", [])}
            registers2 = {item["name"]: item for item in elements2.get("register", [])}

            # 创建图
            dot = graphviz.Digraph(comment="Register Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300", bgcolor="white")

            # 添加寄存器节点
            for name in set(registers1.keys()) | set(registers2.keys()):
                if name in registers1 and name in registers2:
                    if registers1[name] != registers2[name]:
                        # 修改的节点 - 使用#ffffa6
                        label = f"{name}\nOffset: {registers1[name].get('address', 'N/A')} → {registers2[name].get('address', 'N/A')}\nSize: {registers1[name].get('size', 'N/A')} → {registers2[name].get('size', 'N/A')}\nAccess: {registers1[name].get('access', 'N/A')} → {registers2[name].get('access', 'N/A')}"
                        dot.node(
                            name, 
                            label, 
                            shape="box", 
                            style="filled", 
                            fillcolor="#ffffa6"
                        )
                    else:
                        # 未修改的节点 - 使用#ffffff
                        label = f"{name}\nOffset: {registers1[name].get('address', 'N/A')}\nSize: {registers1[name].get('size', 'N/A')}\nAccess: {registers1[name].get('access', 'N/A')}"
                        dot.node(
                            name,
                            label,
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff"
                        )
                elif name in registers1:
                    # 删除的节点 - 使用#ffa6a6
                    label = f"{name}\nOffset: {registers1[name].get('address', 'N/A')}\nSize: {registers1[name].get('size', 'N/A')}\nAccess: {registers1[name].get('access', 'N/A')}"
                    dot.node(
                        name, 
                        label, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#ffa6a6"
                    )
                else:
                    # 新增的节点 - 使用#a6ffa6
                    label = f"{name}\nOffset: {registers2[name].get('address', 'N/A')}\nSize: {registers2[name].get('size', 'N/A')}\nAccess: {registers2[name].get('access', 'N/A')}"
                    dot.node(
                        name, 
                        label, 
                        shape="box", 
                        style="filled", 
                        fillcolor="#a6ffa6"
                    )

                # 添加字段节点
                if name in registers1:
                    for field in registers1[name].get("fields", []):
                        field_name = f"{name}_{field['name']}"
                        # 检查在新版本中是否存在相同的字段
                        field_in_v2 = None
                        if name in registers2:
                            for f2 in registers2[name].get("fields", []):
                                if f2["name"] == field["name"]:
                                    field_in_v2 = f2
                                    break

                        if field_in_v2:
                            # 检查是否有变化
                            if field != field_in_v2:
                                # 修改的字段 - 使用#ffffa6
                                label = f"{field['name']}\nBits: {field.get('bitOffset', 'N/A')} → {field_in_v2.get('bitOffset', 'N/A')}\nWidth: {field.get('bitWidth', 'N/A')} → {field_in_v2.get('bitWidth', 'N/A')}\nAccess: {field.get('access', 'N/A')} → {field_in_v2.get('access', 'N/A')}"
                                dot.node(
                                    field_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffa6"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, field_name, color="#000000", style="solid")
                            else:
                                # 未修改的字段 - 使用#ffffff
                                label = f"{field['name']}\nBits: {field.get('bitOffset', 'N/A')}\nWidth: {field.get('bitWidth', 'N/A')}\nAccess: {field.get('access', 'N/A')}"
                                dot.node(
                                    field_name,
                                    label,
                                    shape="box",
                                    style="filled",
                                    fillcolor="#ffffff"
                                )
                                # 未修改的连接 - 使用#000000
                                dot.edge(name, field_name, color="#000000", style="solid")
                        else:
                            # 删除的字段 - 使用#ffa6a6
                            label = f"{field['name']}\nBits: {field.get('bitOffset', 'N/A')}\nWidth: {field.get('bitWidth', 'N/A')}\nAccess: {field.get('access', 'N/A')}"
                            dot.node(
                                field_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#ffa6a6"
                            )
                            # 删除的连接 - 使用#ffa6a6
                            dot.edge(name, field_name, color="#ffa6a6", style="solid")

                if name in registers2:
                    for field in registers2[name].get("fields", []):
                        field_name = f"{name}_{field['name']}"
                        # 检查在旧版本中是否存在相同的字段
                        field_in_v1 = None
                        if name in registers1:
                            for f1 in registers1[name].get("fields", []):
                                if f1["name"] == field["name"]:
                                    field_in_v1 = f1
                                    break

                        if not field_in_v1:
                            # 新增的字段 - 使用#a6ffa6
                            label = f"{field['name']}\nBits: {field.get('bitOffset', 'N/A')}\nWidth: {field.get('bitWidth', 'N/A')}\nAccess: {field.get('access', 'N/A')}"
                            dot.node(
                                field_name,
                                label,
                                shape="box",
                                style="filled",
                                fillcolor="#a6ffa6"
                            )
                            # 新增的连接 - 使用#a6ffa6
                            dot.edge(name, field_name, color="#a6ffa6", style="solid")

            dot.format = "png"
            output_path = get_temp_filename("register_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating register diff diagram: {e}")
            return None

    def generate_component_diff_diagram(
        self, elements1, elements2, output_img="component_diff"
    ):
        """生成组件差异图"""
        try:
            # 提取组件信息
            comp1 = elements1.get("component", [{}])[0]
            comp2 = elements2.get("component", [{}])[0]

            dot = graphviz.Digraph(comment="Component Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加组件节点
            if comp1:
                label1 = f"{comp1.get('name', 'N/A')}\nVersion: {comp1.get('version', 'N/A')}\nVendor: {comp1.get('vendor', 'N/A')}"
                dot.node(
                    "comp1", label1, shape="box", style="filled", fillcolor="lightblue"
                )

            if comp2:
                label2 = f"{comp2.get('name', 'N/A')}\nVersion: {comp2.get('version', 'N/A')}\nVendor: {comp2.get('vendor', 'N/A')}"
                dot.node(
                    "comp2", label2, shape="box", style="filled", fillcolor="lightgreen"
                )

            # 添加差异连接
            if comp1 and comp2:
                if comp1 != comp2:
                    dot.edge("comp1", "comp2", label="Modified", color="orange")
                else:
                    dot.edge("comp1", "comp2", label="Unchanged", color="gray")

            dot.format = "png"
            output_path = get_temp_filename("component_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"Error generating component diff diagram: {e}")
            return None

    def _generate_diff_table(self, section, elements1, elements2):
        """生成差异表格"""
        try:
            if not elements1 and not elements2:
                return "<p>No elements found in this section.</p>"

            # 特殊处理component元素
            if section == "component":
                comp1_list = elements1.get("component", [])
                comp2_list = elements2.get("component", [])
                comp1 = comp1_list[0] if comp1_list else {}
                comp2 = comp2_list[0] if comp2_list else {}

                html = [
                    "<table class='diff-table'>",
                    "<tr><th>Property</th><th>Version 1</th><th>Version 2</th><th>Status</th></tr>",
                ]

                # 比较组件属性
                for prop in ["name", "version", "vendor", "library"]:
                    v1 = comp1.get(prop, "N/A")
                    v2 = comp2.get(prop, "N/A")
                    if v1 != v2:
                        html.append("<tr class='modified'>")
                        html.append(f"<td>{prop}</td>")
                        html.append(f"<td>{v1}</td>")
                        html.append(f"<td>{v2}</td>")
                        html.append("<td>Modified</td>")
                    else:
                        html.append("<tr>")
                        html.append(f"<td>{prop}</td>")
                        html.append(f"<td>{v1}</td>")
                        html.append(f"<td>{v2}</td>")
                        html.append("<td>Unchanged</td>")
                    html.append("</tr>")

                html.append("</table>")
                return "\n".join(html)

            # 其他元素的处理
            else:
                items1 = {item["name"]: item for item in elements1.get(section, [])}
                items2 = {item["name"]: item for item in elements2.get(section, [])}

                html = [
                    "<table class='diff-table'>",
                    "<tr><th>Name</th><th>Version 1</th><th>Version 2</th><th>Status</th></tr>",
                ]

                all_names = set(items1.keys()) | set(items2.keys())
                for name in sorted(all_names):
                    if name in items1 and name in items2:
                        if items1[name] != items2[name]:
                            html.append("<tr class='modified'>")
                            html.append(f"<td>{name}</td>")
                            html.append(
                                f"<td>{json.dumps(items1[name], indent=2)}</td>"
                            )
                            html.append(
                                f"<td>{json.dumps(items2[name], indent=2)}</td>"
                            )
                            html.append("<td>Modified</td>")
                        else:
                            html.append("<tr>")
                            html.append(f"<td>{name}</td>")
                            html.append(
                                f"<td>{json.dumps(items1[name], indent=2)}</td>"
                            )
                            html.append(
                                f"<td>{json.dumps(items2[name], indent=2)}</td>"
                            )
                            html.append("<td>Unchanged</td>")
                    elif name in items1:
                        html.append("<tr class='removed'>")
                        html.append(f"<td>{name}</td>")
                        html.append(f"<td>{json.dumps(items1[name], indent=2)}</td>")
                        html.append("<td>N/A</td>")
                        html.append("<td>Removed</td>")
                    else:
                        html.append("<tr class='added'>")
                        html.append(f"<td>{name}</td>")
                        html.append("<td>N/A</td>")
                        html.append(f"<td>{json.dumps(items2[name], indent=2)}</td>")
                        html.append("<td>Added</td>")
                    html.append("</tr>")

                html.append("</table>")
                return "\n".join(html)
        except Exception as e:
            print(f"Error generating diff table for {section}: {str(e)}")
            return f"<p>Error generating diff table: {str(e)}</p>"

    def generate_bus_definition_diff_diagram(
        self, elements1, elements2, output_img="bus_definition_diff"
    ):
        """生成总线定义差异图"""
        try:
            # 提取节点信息
            nodes1 = {item["name"]: item for item in elements1.get("busdefinition", [])}
            nodes2 = {item["name"]: item for item in elements2.get("busdefinition", [])}

            # 提取总线接口信息
            interfaces1 = {}
            for item in elements1.get("businterface", []):
                # 使用接口名称作为键，并确保type字段正确设置
                name = item.get("name", "")
                if not name:  # 跳过没有名称的接口
                    continue

                # 获取总线类型，如果不存在则使用接口名称
                bus_type = item.get("type")
                if bus_type is None:
                    bus_type = name

                interfaces1[name] = {
                    "name": name,
                    "type": bus_type.lower() if bus_type else name.lower(),
                    "mode": item.get("mode", "unknown"),
                }

            interfaces2 = {}
            for item in elements2.get("businterface", []):
                # 使用接口名称作为键，并确保type字段正确设置
                name = item.get("name", "")
                if not name:  # 跳过没有名称的接口
                    continue

                # 获取总线类型，如果不存在则使用接口名称
                bus_type = item.get("type")
                if bus_type is None:
                    bus_type = name

                interfaces2[name] = {
                    "name": name,
                    "type": bus_type.lower() if bus_type else name.lower(),
                    "mode": item.get("mode", "unknown"),
                }

            # 创建图
            dot = graphviz.Digraph(comment="Bus Definition Differences", engine="dot")
            dot.attr(rankdir="TB", dpi="300")

            # 添加节点
            for name in set(nodes1.keys()) | set(nodes2.keys()):
                if name in nodes1 and name in nodes2:
                    if nodes1[name] != nodes2[name]:
                        # 修改的节点
                        dot.node(
                            name,
                            f"{name}\nVersion: {nodes1[name]['version']} → {nodes2[name]['version']}",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffa6",
                        )
                    else:
                        # 未修改的节点
                        dot.node(
                            name,
                            f"{name}\nVersion: {nodes1[name]['version']}",
                            shape="box",
                            style="filled",
                            fillcolor="#ffffff",
                        )
                elif name in nodes1:
                    # 删除的节点
                    dot.node(
                        name,
                        f"{name}\nVersion: {nodes1[name]['version']}",
                        shape="box",
                        style="filled",
                        fillcolor="#ffa6a6",
                    )
                else:
                    # 新增的节点
                    dot.node(
                        name,
                        f"{name}\nVersion: {nodes2[name]['version']}",
                        shape="box",
                        style="filled",
                        fillcolor="#a6ffa6",
                    )

            # 添加连接

            # 1. 处理第一个版本中的连接
            for intf1 in interfaces1.values():
                if intf1.get("mode") == "master":
                    master_bus = intf1.get("type", "")
                    if not master_bus:  # 跳过没有类型的接口
                        continue
                    for intf2 in interfaces1.values():
                        if intf2.get("mode") == "slave":
                            slave_bus = intf2.get("type", "")
                            if not slave_bus:  # 跳过没有类型的接口
                                continue
                            if master_bus in nodes1 and slave_bus in nodes1:
                                dot.edge(master_bus, slave_bus, color="#ffa6a6")

            # 2. 处理第二个版本中的连接
            for intf1 in interfaces2.values():
                if intf1.get("mode") == "master":
                    master_bus = intf1.get("type", "")
                    if not master_bus:  # 跳过没有类型的接口
                        continue
                    for intf2 in interfaces2.values():
                        if intf2.get("mode") == "slave":
                            slave_bus = intf2.get("type", "")
                            if not slave_bus:  # 跳过没有类型的接口
                                continue
                            if master_bus in nodes2 and slave_bus in nodes2:
                                dot.edge(master_bus, slave_bus, color="#a6ffa6")

            # 3. 处理共同存在的连接
            for intf1 in interfaces1.values():
                if intf1.get("mode") == "master":
                    master_bus = intf1.get("type", "")
                    if not master_bus:  # 跳过没有类型的接口
                        continue
                    for intf2 in interfaces1.values():
                        if intf2.get("mode") == "slave":
                            slave_bus = intf2.get("type", "")
                            if not slave_bus:  # 跳过没有类型的接口
                                continue
                            if master_bus in nodes1 and slave_bus in nodes1:
                                # 检查在第二个版本中是否存在相同的连接
                                found = False
                                for intf3 in interfaces2.values():
                                    if (
                                        intf3.get("mode") == "master"
                                        and intf3.get("type", "") == master_bus
                                    ):
                                        for intf4 in interfaces2.values():
                                            if (
                                                intf4.get("mode") == "slave"
                                                and intf4.get("type", "") == slave_bus
                                            ):
                                                found = True
                                                break
                                        if found:
                                            break
                                if found:
                                    dot.edge(master_bus, slave_bus, color="#000000")

            # 生成图片
            dot.format = "png"
            output_path = get_temp_filename("bus_definition_diff", "")
            dot.render(output_path, cleanup=True)
            img_path = output_path + ".png"

            # 转换为base64
            base64_str = image_to_base64(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            return base64_str
        except Exception as e:
            print(f"生成总线定义差异图时出错: {e}")
            return None
