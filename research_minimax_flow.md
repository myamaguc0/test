# 最小極大流（Minimax Flow）調査レポート

調査日: 2026-03-17

---

## 1. 概要

**最小極大流（Minimax Flow）** とは、ネットワークフロー最適化の一分野であり、ネットワーク内の各リンク（辺）に流れるフローの最大値を最小化する問題である。通常の最大フロー問題が「できるだけ多く流す」ことを目的とするのに対し、最小極大流問題は「最も負荷の高いリンクの負荷を最小化する（ボトルネックを緩和する）」ことを目的とする。

### 直感的な理解

- 最短路にフローを集中させると、ボトルネックリンクで渋滞が発生する
- 最小極大流は、トラフィックをネットワーク全体に分散させ、最も利用率の高いリンクの負荷を最小化する
- p-ノルムコスト関数において p → ∞ としたときの最適解が最小極大流に対応する

---

## 2. 数学的定式化

### 2.1 基本的な定式化

**ネットワーク**: 有向グラフ G = (V, E)、各辺 (i,j) に容量 c_ij

**目的関数**:
```
minimize  max_{(i,j) ∈ E} f_ij
```

**制約条件**:
- フロー保存則: 各ノードについて、流入量 = 流出量（ソース・シンクを除く）
- 容量制約: 0 ≤ f_ij ≤ c_ij（各辺について）

### 2.2 Minimax Transportation Problem（最小極大輸送問題）

Ahuja (1986) による定式化:

```
minimize  max_{(i,j)} { c_ij × x_ij }
```

- I: 供給地の集合、J: 需要地の集合
- x_ij: 供給地 i から需要地 j への輸送量
- c_ij: 単位輸送コスト
- 供給量・需要量の制約を満たしつつ、最大コストを最小化する

### 2.3 p-ノルム近似による定式化

p-ノルムコスト関数:
```
minimize  (Σ_{(i,j) ∈ E} |f_ij|^p)^{1/p}
```

p → ∞ のとき、この最適化は minimax コスト関数の最小化に収束する。

---

## 3. 関連する基礎概念

### 3.1 最大フロー問題（Maximum Flow Problem）

- **定義**: ソース s からシンク t への最大フローを求める問題
- **歴史**: 1954年、T.E. Harris と F.S. Ross がソビエト鉄道のトラフィックモデルとして定式化
- **主要アルゴリズム**:

| アルゴリズム | 計算量 | 備考 |
|---|---|---|
| Ford-Fulkerson法 | O(E × f*) | 増加路法、f*は最大フロー値 |
| Edmonds-Karp法 | O(V × E²) | BFSによる増加路探索 |
| Dinic法 | O(V² × E) | ブロッキングフロー |
| Push-Relabel法 | O(V² × E) | Goldberg-Tarjan |
| Binary Blocking Flow | O(E × min(E^{1/2}, V^{2/3})) | Goldberg-Rao |
| Almost-Linear Time (2022) | m^{1+o(1)} | Chen et al. |

### 3.2 最大フロー最小カット定理（Max-Flow Min-Cut Theorem）

**定理**: ネットワークにおける s-t 最大フローの値は、s-t 最小カットの容量に等しい。

- **最小カット**: グラフを s を含む集合 S と t を含む集合 T に分割したとき、S から T への辺の容量の合計が最小となる分割
- フローのボトルネックは最小カットによって決まる
- 残余グラフ上で s から到達可能な頂点集合 S を求めることで最小カットを特定できる

### 3.3 最小費用流問題（Minimum Cost Flow）

- 「決まった量のものを、できるだけ小さいコストで運ぶ」問題
- 最短路問題と最大流問題の共通の一般化
- 最小極大流問題とは異なり、総コストの最小化が目的

---

## 4. 最小極大流のアルゴリズム

### 4.1 パラメトリックアルゴリズム（Ahuja, 1986）

- パラメトリック上界を持つ輸送問題を解く
- 上界パラメータを徐々に下げながら実行可能解を探索

### 4.2 主双対アルゴリズム（Ahuja, 1986）

- 一連の関連する最大流問題を逐次的に解く
- 各反復で最大フローアルゴリズムを用いて実行可能性を判定

### 4.3 分散アルゴリズム（Coraggio et al., 2022）

- **対象**: 非巡回グラフ上の minimax flow
- **手法**: 最大下流フロー間のコンセンサス問題として再定式化
- **応用**: マイクログリッドにおける過電流防止のためのオンライン分散コントローラ
- 可変供給者と固定消費者を持つフローネットワークにおいて、ノード間の最大フローを最小化

### 4.4 逐次二次計画法（SQP）ベース（Anaraki & Kalantari, 2011）

- コスト関数を二次関数で近似し、ヤコビ法で二次最適化を解く
- p-ノルムコスト関数に適用
- 分散実装が可能

### 4.5 緩和法ベース（Relaxation-based）

- 各反復で緩和されたminimax問題を解く
- 最適解またはより良い下界を提供
- 実行可能性テストに最大流アルゴリズムを使用

---

## 5. 応用分野

### 5.1 通信ネットワーク
- **ATMネットワークルーティング**: 全リンクの最大セル損失確率を最小化するルーティング最適化（Lee & Yee, 1994）
- マルチコモディティフロー問題として定式化

### 5.2 電力システム（マイクログリッド）
- ドループ制御インバータと負荷からなるマイクログリッドでの過電流防止
- オンライン分散制御アルゴリズムによる実装

### 5.3 輸送最適化
- 輸送コストのボトルネック最小化
- 施設配置問題（rectilinear距離）

### 5.4 資源配分
- ネットワーク上のリソース割当て最適化
- 負荷分散（ロードバランシング）

---

## 6. 関連問題との関係

```
最短路問題 ──────┐
                  ├──→ 最小費用流問題
最大流問題 ──────┘         │
    │                      │
    ├──→ 最小カット問題     │
    │                      │
    ├──→ 二部マッチング     │
    │                      │
    └──→ 最小極大流問題 ←──┘
              │
              ├──→ ボトルネック最短路
              ├──→ minimax輸送問題
              └──→ minimax ルーティング
```

---

## 7. 主要参考文献

### 学術論文
1. **Ahuja, R.K.** (1986). "Algorithms for the minimax transportation problem." *Naval Research Logistics Quarterly*, 33(4), 725-739.
2. **Coraggio, M. et al.** (2022). "Minimax Flow over Acyclic Networks: Distributed Algorithms and Microgrid Application." arXiv:2201.03310.
3. **Anaraki & Kalantari** (2011). "Acceleration of Distributed Minimax Flow Optimization in Networks." *CISS 2011*, IEEE.
4. **Lee, T.T. & Yee, J.R.** (1994). "An algorithm for optimal minimax routing in ATM networks." *Annals of Operations Research*.
5. **Ahuja, R.K.** (1985). "Minimax linear programming problem." *Operations Research Letters*.
6. **Chen et al.** (2022). "Maximum Flow and Minimum-Cost Flow in Almost-Linear Time." arXiv:2203.00671.

### Webリソース
- [最大フロー問題 - Wikipedia (日本語)](https://ja.wikipedia.org/wiki/%E6%9C%80%E5%A4%A7%E3%83%95%E3%83%AD%E3%83%BC%E5%95%8F%E9%A1%8C)
- [最大フロー最小カット定理 - Wikipedia (日本語)](https://ja.wikipedia.org/wiki/%E6%9C%80%E5%A4%A7%E3%83%95%E3%83%AD%E3%83%BC%E6%9C%80%E5%B0%8F%E3%82%AB%E3%83%83%E3%83%88%E5%AE%9A%E7%90%86)
- [Maximum flow problem - Wikipedia (English)](https://en.wikipedia.org/wiki/Maximum_flow_problem)
- [ネットワークフロー問題たちの関係を俯瞰する](https://theory-and-me.hatenablog.com/entry/2021/04/15/171702)
- [ネットワークフロー入門 (保坂和宏)](https://hos.ac/slides/20150319_flow.pdf)
- [最大流で解ける問題 - 37zigen](https://37zigen.com/max-flow/)
- [極める！最大流千本ノック - Qiita](https://qiita.com/NAMIDAIRO/items/e2edb6b54e1c6e68c6c2)
- [Stanford CS161 Lecture 16 - Max Flow](https://web.stanford.edu/class/archive/cs/cs161/cs161.1168/lecture16.pdf)
- [Princeton Network Flow Slides](https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/07NetworkFlowI.pdf)
- [Google OR-Tools Maximum Flows](https://developers.google.com/optimization/flow/maxflow)

---

*本レポートは、Web検索による調査結果に基づいて作成されました。*
