# 建模与公式依据追踪表

本表区分三类内容：“采用”表示直接使用已有标准模型；“改写”表示在已有模型上为本文场景作可核验变换；“原创”表示本文新命题，必须由正文证明而不能仅用引用代替。文献键与 `references.bib` 完全一致。

| 编号 | 建模或公式 | 性质 | 文献依据 | 本文必须说明的边界 |
|---|---|---|---|---|
| M1 | 历史日基线及事件响应 \(\hat p_t-p_t^{\mathrm{event}}\) | 采用 | CAISO 的历史日基线规则 \cite{caiso2017baseline} | High-5-of-10 是审查用代表性规则，不宣称复刻任一市场的全部日型筛选与当日修正条款。 |
| M2 | 基线操纵的期望收益 \(q\pi^{\mathrm{DR}}\Delta B-\sum_{j=1}^{10}\Delta C_j\) | 改写 | 基线内生操纵问题 \cite{wang2022baseline} | 十日平均只作用于奖励基线；十个参考日的物理成本必须求和。本文将多期行为写成十个参考日上的确定性等价线性规划，概率、价格和参考日数量均显式给出。 |
| P1 | 边际操纵条件 \(q\pi^{\mathrm{DR}}/10>\min_j c'_j\) | 原创特例推导 | 问题动机来自 \cite{wang2022baseline}；右端项影子价格依据线性规划对偶理论 \cite{boyd2004convex} | \(c'_j\) 由诚实调度中事件服务下界的对偶边际值独立计算；正文必须区分严格不等式、等号处多重最优调度和严格获利，不能从战略求解结果反推阈值。 |
| M3 | 延迟容忍任务、完成期限、容量和跨地域服务变量 | 采用并扩展 | 数据中心工作负载移峰、需求响应与批任务灵活性评估 \cite{cao2022flexibility} | 来源支持可延迟任务与期限约束；四地域和三服务类别是本文实验设定，不具有外部统计代表性。 |
| P2 | 累计状态约束 \(y_{skt}\le A_{skt}\)、\(y_{skt}\ge A_{sk,t-D_k}\) | 原创等价改写 | 基础期限调度见 \cite{cao2022flexibility} | 本文必须证明累计状态形式与逐任务释放—期限可行性等价，并报告终端守恒条件。 |
| M3b | 连续滚动终端条件 \(y_{skT^+}=A_{sk,\max\{T^0,T^+-D_k\}}\) 与两阶段词典序轨迹嵌入 | 采用并扩展 | 滚动时域数据中心调度依据 \cite{zhang2023receding}；最优面与绝对值上图依据 \cite{boyd2004convex} | 窗口保留全部真实未来到达，不补零、不循环复制；第一阶段只最小化轨迹 L1 距离，第二阶段在该最优面最小化运行成本，数值容差必须显式审计。 |
| C2 | 可行解凸组合仍可行 | 采用并实例化 | 凸集与仿射约束的标准性质 \cite{boyd2004convex} | 引用支撑一般性质；本文还必须逐项确认六个投影共享同一到达量和同一线性可行域。 |
| P2.2 | 总暴露—日尾部条件风险约束与点式安全包络 | 原创方法与推论 | 凸二次规划与正部函数依据 \cite{boyd2004convex}；条件风险价值依据 \cite{rockafellar2000cvar} | 验证问题同时约束总虚假信用与日级 75% 条件风险价值；\(\beta\) 只通过连续时间折叠选择。最终再解一个带 \(p^{\rm safe}_{dt}\le p^{(\ell^\star)}_{dt}\) 事件上界的完整任务规划，由正部函数单调性得到相对于所选工作负载可行参考的逐点虚假信用 MWh 非劣保证；这不等同于对任意运营商无事件电表的分布无关预测覆盖。双侧带的下界与额外欠信用上界见 P2.2b，不使用测试标签。 |
| M4 | 直流 SCED：节点平衡、线路潮流、机组上下限和分段线性成本 | 采用 | MATPOWER/PYPOWER 的网络与二次成本模型 \cite{zimmerman2011matpower}；PGLib 标准测试数据 \cite{babaeinejadsarookolaee2021pglib} | 这是无损直流近似，不得外推为交流可行性。两层均保留 PGLib 拓扑、容量和线路额定值，并按完全一致的 54 个机组节点使用公开 PYPOWER IEEE-118 二次成本；市场结算使用 10 段，独立评分重新求解 80 段，二者不能混称为同一“精确真值”。 |
| P2.2b | 双侧信用带 \(p^{(\ell^\star)}-\varepsilon\leq p^{\rm safe}\leq p^{(\ell^\star)}\) | 原创方法与推论 | 正部函数单调性与凸可行域依据 \cite{boyd2004convex} | 事件上界保留虚假信用非劣性；固定 \(\varepsilon\) 的下界排除零信用退化，并将额外欠信用上界为 \(\varepsilon|\mathcal D||\mathcal E|\Delta t\)。命题 2 和实验 2 同时审计两侧点式裕度。 |
| M4b | N--1 线路故障后潮流 \(f_\ell^{(k)}=(H_\ell+L_{\ell k}H_k)(C_gg-p)\) | 采用并完整实例化 | 直流潮流与 PTDF/LODF 定义 \cite{stott2009dc}；基于 LODF 的安全约束调度 \cite{tejada2018lodf}；N--1 规划准则 \cite{nerc2020tpl} | 第 8 个实验同时加入全部有限的非孤岛单线路故障约束，不做故障筛选、线路降额或结果条件化选择；孤岛故障由于单参考节点 PTDF 无法表示而单独报告。公开 RTS-24 数据依据 \cite{grigg1999rts}。 |
| P4 | 多场景支付证书：把每个事件时段、每个功率换算场景的完整 N--1 调度原始可行域嵌入反事实选择，并分别约束日成本不超过同场景参考反事实 | 原创方法与确定性推论 | SCED 原始模型依据 \cite{zimmerman2011matpower}；线性规划值函数、上图形式和词典序求解依据 \cite{boyd2004convex}；换算场景来自留出 MIT DCGM 作业级实测能量 \cite{samsi2021supercloud} | 候选集由六个独立求解的一阶段可行投影及最强匹配可行分位数投影构成；风险约束验证器只是证书目标，不允许直接作为候选。第一层线性规划最小化目标轨迹偏差，第二层保持该最优值并最大化三种场景的共同成本裕度。有限场景固定为留出作业“实测/预测能量比”的第 10、50、90 百分位，不根据测试结果筛选。可行分位数参考的单位权重证明各场景可行，场景内实际事件成本在两种支付中相消。保证仅针对声明的有限场景，不外推为连续分布鲁棒保证。 |
| M4c | 非线性交流最优潮流：有功/无功平衡、电压、无功出力和视在功率线路限制 | 采用并用于模型外验证 | MATPOWER 交流最优潮流及 IEEE-9/14 系统数据 \cite{zimmerman2011matpower} | 第 10 个实验先在四个公开网络和全部锁定日上重新求解基态交流最优潮流，再对 IEEE-9 的全部 6 个和 IEEE-14 的全部 19 个非孤岛线路故障逐一求解故障后交流最优潮流。第 18 个实验在 RTS-24、IEEE-30、IEEE-39、IEEE-118 上固定 0.90 原生负荷倍率、3/6/9% 渗透率和六个预注册快照，把基态非参考机组有功出力作为等式边界固定到每一个连通有限事故场景，只允许参考机组承担网损差及无功/电压补救；该面板是预防性有功计划稳态验证，不是动态稳定证明。 |
| M5 | 节点边际价格为 SCED 节点平衡约束的对偶边际值 | 采用 | 最优潮流和对偶价格模型 \cite{zimmerman2011matpower,boyd2004convex} | 节点价格仅对当前凸、连续 SCED 有效；不含启停、损耗和非凸报价。 |
| M5b | 完整响应周期的时空节点补偿 \(\Pi^{\rm ST}=\Delta t\sum_{d,t\in\mathcal W}\lambda^0_{dt}(p^0_{dt}-p^1_{dt})\) | 采用并用于验证后结算 | 虚拟链路市场清算 \cite{zhang2020virtuallinks}；时空移载补偿 \cite{zhang2022remunerating} | \(\mathcal W\) 同时包含事件前转移、事件时段与最长期限恢复；站点分配之和必须等于总补偿，且必须与双边避免成本合同 \(\Delta V\) 明确区分。 |
| M5c | 需求响应容量产品 \(Q^{\rm cap}\)、总运营者价值 \(G=r^{\rm DR}Q^{\rm cap}+\Pi^{\rm ST}\) 与带不成交外部选择的对称纳什分配 | 采用并组合 | 需求响应容量信用及事后个体理性 \cite{satchidanandan2023twostage}；空间耦合数据中心激励相容需求响应 \cite{chen2021incentive}；对称议价解 \cite{nash1950bargaining} | 容量服务只在预先声明的参与站点和事件窗口按预先声明价格计量；节点能量项仍对迁移与恢复做有符号记账。机会成本必须相对于相同真实到达窗口的无事件最优调度。总剩余为负时执行不成交外部选择；总剩余非负时双方各得 \(S/2\)，不得把节点报酬冒充完整合同支付。 |
| P3 | 线性节点结算与精确价值差之间的多面体 Bregman 间隙 | 原创应用命题 | 价值函数和次梯度理论 \cite{boyd2004convex} | 对实际实现的分段线性 SCED，证明全局不等式 \(0\leq\Delta V_{\rm lin}-\Delta V\leq\lVert \lambda^1-\lambda^0\rVert_*\lVert p^1-p^0\rVert\)，并用 \(\lambda\) 表示节点价值次梯度、用 \(g\) 表示发电，消除符号冲突。 |
| M6 | 四站点及八合同组合的特征函数 \(v(S)\) | 原创应用定义 | 合作博弈框架 \cite{shapley1953value} | SCED 混合负荷如何构造必须逐联盟明确定义；八参与者组合份额仅用测试期之前的公开任务到达量确定。该价值函数不是文献直接提供。 |
| M6b | Shapley 分摊公式、效率与同站点可交换合同的精确计数状态求和 | 采用定理、本文实现 | Shapley 原始定义与效率性质 \cite{shapley1953value} | 四/八参与者保留逐联盟枚举；4--20 参与者只在同一电气站点内的合同切片可交换时使用二项式重数精确合并，不是抽样或近似。 |
| M7 | 岭回归、梯度提升树、极端随机树、分位数提升树和合成控制 | 采用 | 岭回归与梯度提升依据 \cite{hoerl1970ridge,friedman2001gradient}；极端随机树与合成控制依据 \cite{geurts2006extratrees,abadie2010synthetic} | 这些是基线，不是本文创新；超参数、特征、信息时点、供体窗口和训练窗口必须在实验设置完整报告。 |
| M8 | 移动区块自助置信区间与区块符号随机化 | 采用并实例化 | 相关序列的区块重采样 \cite{kunsch1989bootstrap} | 主分析使用 18 个互不重叠的三日区块并枚举 \(2^{18}\) 个符号；同时报告 6、9、18 日区块敏感性，不能把相邻日当成独立样本。 |
| M9 | Holm 逐步校正 | 采用 | \cite{holm1979multiple} | 分别在 nRMSE、虚假响应比例和信用识别 \(F_1\) 三个预先声明的结果族内，对四个比较控制家族错误率。 |
| M10 | 稀疏线性规划的全局最优数值求解 | 采用 | HiGHS 对偶修正单纯形实现 \cite{huangfu2018highs} | 求解器成功状态、原始可行性证书和独立约束残差必须同时通过；数值最优不替代模型有效性证明。 |
| D1 | BurstGPT 请求到达、令牌数和服务类型 | 采用数据 | \cite{wang2024burstgpt} | 公开数据没有设施功率和地理位置；令牌到功率的缩放是本文场景参数。 |
| D2 | MIT Supercloud 调度日志和 DCGM 测量 | 采用数据 | \cite{samsi2021supercloud} | 提交时间形成到达，执行期 DCGM 能量形成独立评分真值；它与 BurstGPT 不是同一运营商或同一地点。 |
| D3 | 四条区域轨迹到四个电气接入点的对应关系及峰值功率尺度 | 本文实验设计，不是外部事实 | 公共网络数据依据 \cite{babaeinejadsarookolaee2021pglib}；计算轨迹依据 \cite{wang2024burstgpt,samsi2021supercloud} | 第 11 个实验穷举全部 \(4!=24\) 种对应关系，并与 3%、6%、9% 三个预声明峰值渗透率和全部锁定日做笛卡尔积。第 21 个实验另行报告固定 0.001-MW/GPU 可部署尺度与容量同比例 stress scale；后者不替代部署证书。该实验检验结论对空间对应和尺度的敏感性，但不能把非共址公开数据升级为现场测量。 |

## 正文公式标签逐一追踪

下表与 `main.tex` 中全部 30 个带编号公式标签一一对应。“本文推导”表示不能用外部文献替代证明，正文必须给出命题、假设与证明；“标准模型”或“标准工具”表示正文首次使用时必须引用所列来源。

| 正文标签 | 对应条目 | 依据或证明位置 |
|---|---|---|
| `eq:cumulative` | M3、P2 | 可延迟工作建模依据 \cite{cao2022flexibility}；累计状态等价性由命题 2 及释放—期限约束共同证明。 |
| `eq:ledgerdigest` | P6 | SHA-256 摘要与篡改检测依据 NIST Secure Hash Standard \cite{nist2015fips1804}；规范化任务账本、连接守恒和容量包络证书由命题 6 与实验 16 实现。 |
| `eq:release` | M3、P2 | 释放时刻约束依据 \cite{cao2022flexibility}；累计写法是本文等价改写。 |
| `eq:deadline` | M3、P2 | 完成期限依据 \cite{cao2022flexibility}；累计写法是本文等价改写。 |
| `eq:power` | M3 | 计算服务到设施功率的线性映射依据数据中心负荷调度模型 \cite{cao2022flexibility}。 |
| `eq:rollingterminal` | M3b | 滚动时域状态保留依据 \cite{zhang2023receding}；本文针对真实未来到达给出终端等式并由命题 2 审计可行性。 |
| `eq:falsecredit` | M1、P2.2 | 历史基线与事件响应语境依据 \cite{caiso2017baseline}；提交信用与真实信用分别定义，源特定正部差额由命题 2 证明。观测电表和机制隔离轨迹分开审计，不能把离线 oracle 当成部署输入。 |
| `eq:meter_cap` | P2.3 | 本文可部署结算定义：提交信用、冻结合同 no-event profile credit 与闭合电表 credit 的点式交集；trace-anchored no-event profile 仅用于事后 oracle overpayment/underpayment 诊断，不进入目标拟合、事件门决策或工作负载优化。 |
| `eq:profit` | M2 | 基线内生操纵问题依据 \cite{wang2022baseline}；十参考日确定性等价式是本文场景化改写。 |
| `eq:threshold` | P1 | 线性规划灵敏度依据 \cite{boyd2004convex}；充分必要条件由命题 1 证明。 |
| `eq:sced` | M4 | 标准无损直流经济调度与对偶价格模型依据 \cite{stott2009dc,zimmerman2011matpower}；公开 PGLib 参数依据 \cite{babaeinejadsarookolaee2021pglib}。 |
| `eq:value` | P3 | 基于 `eq:sced` 最优值函数的有符号差定义；与线性结算的关系由命题 3 证明。 |
| `eq:projection` | C2、P2.2 | 绝对值上图与凸投影依据 \cite{boyd2004convex}；工作负载可行域保持性由命题 2 证明。 |
| `eq:totalrisk` | P2.2 | 正部凸约束依据 \cite{boyd2004convex}；风险预算构造为本文方法。 |
| `eq:cvar` | P2.2 | 条件风险价值及其经验上图依据 \cite{rockafellar2000cvar}；与总暴露的联合约束为本文方法。 |
| `eq:riskepigraph` | P2.2 | CVaR 的阈值与尾部松弛上图依据 \cite{rockafellar2000cvar,boyd2004convex}；线性化实现和验证期预算为本文方法。 |
| `eq:envelope` | P2.2 | 点式安全包络为本文方法；相对于所选工作负载可行参考的虚假信用非劣性由命题 2 证明。 |
| `eq:twosided` | P2.2b | 双侧信用带为本文方法；固定 \(\varepsilon\) 的下界防止零信用退化，并由命题 2 同时给出虚假信用非劣性与额外欠信用上界。 |
| `eq:jobnetworkcoupling` | P6、C1 | 同一 indexed job--slot witness 的区域聚合定义；命题 9 证明其与 aggregate profile 的恒等关系，Experiment 22 在 N--1 dispatch 前逐槽检查最大残差。 |
| `eq:causalreserve` | P2.4 | 仅使用历史日的经验分位数 reserve 是本文的决策时间规划定义；它不进入事件支付资格，候选分位数与验证期 false-credit budget 在实验设置中预先声明。 |
| `eq:bregman` | P3 | 凸值函数次梯度不等式依据 \cite{boyd2004convex}；在有符号节点价值中的具体结论由命题 3 证明。 |
| `eq:spacetime` | M5b | 虚拟链路与时空补偿依据 \cite{zhang2020virtuallinks,zhang2022remunerating}。 |
| `eq:capacityservice` | M5c | 需求响应容量信用与事后个体理性依据 \cite{satchidanandan2023twostage,chen2021incentive}。 |
| `eq:operatorvalue` | M5b、M5c | 时空能量项与容量产品的组合定义；两部分分别依据 \cite{zhang2022remunerating,satchidanandan2023twostage}。 |
| `eq:nashcontract` | M5c | 对称纳什议价解依据 \cite{nash1950bargaining}；不成交外部选择和机会成本口径在实验 12 逐日审计。 |
| `eq:n1` | M4b | PTDF/LODF 依据 \cite{stott2009dc,tejada2018lodf}；N--1 规划准则依据 \cite{nerc2020tpl}。 |
| `eq:paymentcert` | P4 | SCED 原始可行域和线性规划上图依据 \cite{zimmerman2011matpower,boyd2004convex}；以验证期选定的单一可行投影为合同参考、以可行分位投影为外部转账比较的多换算场景词典序证书为本文方法。 |
| `eq:paymentdominance` | P4 | 本文确定性推论；由 `eq:paymentcert` 的可行调度上界和同场景实际成本相消得到，完整证明见命题 4。参考对象是验证期选定的单一可行投影，不是分位投影。 |
| `eq:paymentinterval` | P5 | 连续 workload-hull 支付区间是本文的确定性值函数定义与命题 5；有限换算场景和闭区间端点由验证期锁定候选 profile 生成，不宣称概率覆盖。 |
| `eq:shapley` | M6、M6b | Shapley 定义、效率和组合权重依据 \cite{shapley1953value}；有符号调度特征函数为本文实例化。 |
| `eq:acplan` | M4c | 交流最优潮流与公开测试系统依据 \cite{zimmerman2011matpower}；跨事故固定非参考机组有功计划是本文预防性验证边界。 |

## 无外部文献替代、但必须披露的实验参数

四个数据中心位置、6% 峰值渗透率、三类期限、等待成本、令牌功率缩放、MIT 能量缩放、16 日验证集、54 日测试集以及事件窗口均属于本文预先声明的实验设计。它们不能靠引用“证明正确”，而应在正文中给出数值、选择依据、敏感性分析和外推边界。线路额定值来自公开测试系统并保持原值，不能再以人为降额制造拥塞。

## 引用审计规则

完整正文中每个模型首次出现处至少包含一个对应文献键；每个标为“原创”的命题必须包含假设、命题和证明；每个数据转换必须指向数据文献与 `data_manifest.json`；每个算法基线必须同时报告原始算法引用和本文实现参数。缺少其中任一项时，论文不得标记为可投稿版本。

## 近年结构性对照

非输电替代方案、批处理灵活性和空间时间虚拟链路分别由
\cite{cao2024nonwire}、\cite{cao2022flexibility} 和
\cite{zhang2020virtuallinks,zhang2022remunerating} 提供结构性参照。它们用于限定
相关工作与 baseline panel 的比较边界，不被当作本文门控账本、冻结合同
基线或闭合电表结算规则的直接来源；这些规则仍由正文中的定义、命题和
实验审计负责。
