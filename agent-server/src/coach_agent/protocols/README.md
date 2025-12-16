# CBT-based Spending Habit Improvement Protocols

이 디렉토리는 충동적·습관적 소비 패턴을 개선하고, 소비로 인한 정서적·재정적 스트레스를 완화하기 위해 설계된 **CBT 기반 10주 차 코칭 프로토콜(YAML)**을 포함하고 있습니다.

본 프로토콜은 **Compulsive Buying Disorder(CBD)** 및
그에 준하는 충동 소비 문제에 대한 검증된 인지행동치료(CBT) 연구들을 바탕으로, LLM(대규모 언어 모델) 기반 상담 시스템에 적용 가능하도록 구조화·재설계되었습니다.

---

## 🎯 Project Scope & Purpose (기획 의도)

본 프로젝트는 **의료적 치료(Medical Treatment)**가 아닌, **코칭 및 자기 관리(Self-regulation & Coaching)** 목적의 디지털 상담 프로토콜을 제공합니다.

* **Target Audience:**
  병원 치료가 필요한 중증 CBD 환자를 대체하기 위한 서비스가 아니라, 충동적 소비, 스트레스성 지출, 감정 기반 소비 패턴으로 반복적인 어려움을 겪는 성인 사용자를 대상으로 합니다.

* **Goal:**
  임상 CBT에서 효과가 검증된 개입(intervention)과 기법(technique)을 사용자가 스스로 이해하고 연습할 수 있도록 구조화하여, 장기적으로 더 건강한 소비 습관과 감정 조절 능력을 형성하도록 돕습니다.

* **Method:**
  전통적인 CBT 치료 매뉴얼을 그대로 재현하지 않고, 다음과 같은 원칙으로 **경량화(Lite)** 및 **재구성(Re-engineering)** 하였습니다.
  * 고정된 세션 스크립트 대신 **세션 목표·성공 기준 중심 설계**
  * LLM이 상황에 따라 CBT 기법을 선택·적용하는 **동적 개입 구조**
  * 자기 관찰(Self-monitoring)과 행동 실험(Behavioral Experiment)을
    중심으로 한 **학습형 코칭 모델**

---

## 📚 References & Credits (참고 문헌 및 크레딧)

본 프로토콜은 아래의 임상 연구 및 CBT 교과서를 이론적·구조적 기반으로 삼아 개발되었습니다. 본 프로젝트는 특정 저작물을 복제하지 않으며, AI 상담 시스템에 적합하도록 **개념·구조·치료 원칙을 재해석**한 것입니다.

---

### 1. `week{n}.yaml`: Structural Framework & Treatment Flow  

(프로그램 구조 및 회기 설계)

본 10주 프로토콜의 전체 흐름, 세션 배치, 치료 단계 구성은 다음 연구들을 핵심 근거로 합니다.

* **Mitchell, J. E., Burgard, M., Faber, R. J., Crosby, R. D., & de Zwaan, M. (2006).**  
  *Cognitive behavioral therapy for compulsive buying disorder.*  
  *Behavior Research and Therapy, 44(12), 1859–1865.*

* **Leite, P. L., Rangé, B. P., Ribas, R. C., & de Menezes, G. B. (2014).**  
  *Cognitive-behavioral group therapy for compulsive buying disorder: A systematic review.*  
  *Revista Brasileira de Psiquiatria.*

**적용된 핵심 요소:**

* 10주 치료 구조 (12-session model의 10주 재배치)
* 소비 촉발 요인(Cues) 및 결과(Consequences) 분석
* 금전 관리(Money Management) 및 접근성 제한
* 인지 재구조화(Cognitive Restructuring)
* 노출 및 반응예방(Exposure & Response Prevention, ERP)
* 스트레스 관리 및 문제 해결
* 재발 방지(Relapse Prevention) 및 유지 계획

---

### 2. `techniques.yaml`: Core CBT Techniques & Clinical Principles  

(CBT 기법 및 이론적 원칙)

본 프로토콜의 모든 개입(intervention)과 기법 선택 기준은 다음 CBT 교과서를 중심으로 정립되었습니다.

* **Beck, J. S. (2011).**  
  *Cognitive Behavior Therapy: Basics and Beyond (2nd / 3rd ed.).*  
  Guilford Press.

**반영된 CBT 핵심 기법:**

* Automatic Thought Identification
* Guided Discovery & Socratic Questioning
* Behavioral Chain Analysis
* Cognitive Restructuring (Evidence For/Against)
* Downward Arrow (Belief Exploration)
* Behavioral Experiment
* Exposure & Response Prevention
* Problem Solving & Coping Skills Training
* Relapse Prevention Planning

이 교과서는 본 프로젝트에서 **기법 정의, 질문 방식, 세션 진행 원칙의 표준(reference)** 역할을 합니다.

---

### 3. Conceptual Orientation & Counseling Attitude  

(상담 태도 및 개념적 방향성)

본 프로토콜은 전통적인 CBT의 구조를 유지하면서도, 비판·통제 중심 접근이 아닌 **자기 인식과 자기 조절(self-regulation)**을 강조하는 방향으로 설계되었습니다.

* **적용된 핵심 관점**
  * 소비 행동을 “의지 부족”이 아닌 **학습된 정서 조절 전략**으로 이해
  * 실패(lapse)를 치료 실패가 아닌 **데이터와 학습 기회**로 해석
  * 자기 비난 대신 **관찰·이해·선택**을 강조하는 코칭 태도

이는 임상 CBT의 핵심 원칙을 훼손하지 않으면서,
LLM 기반 상담 환경에 적합하도록 재구성된 접근입니다.

---

## ⚠️ Disclaimer (면책 조항)

1. **Not Medical Advice**  
   본 프로토콜은 의료적 진단이나 치료를 제공하지 않습니다.
   심각한 재정 문제, 중독 수준의 소비, 우울증·불안장애 등 임상적 개입이 필요한 경우, 반드시 정신건강의학과 전문의 또는 임상 심리 전문가의 도움을 받아야 합니다.

2. **Educational & Technical Use**  
   본 리포지토리는 LLM 기반 상담 시스템에서 CBT 프로토콜을 구조화·운영하는 방법을 보여주는 **기술적 구현 예시(Technical Implementation)**입니다. 원문 저작물을 그대로 복제하지 않았으며, AI 에이전트용 지침(prompt & protocol)으로 재해석된 **2차적·변형적 저작물**의 성격을 가집니다.
