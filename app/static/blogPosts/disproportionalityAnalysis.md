## Introduction

For the last few years, I have been working at Uppsala Monitoring Centre (UMC), a non-profit and WHO collaborating centre. At UMC we are concerned with adverse drug reactions (ADRs), which are unintended, harmful reactions to medication. We constantly monitor our database of, at the time of writing, over 33 million reports of adverse drug reactions to find new, rare and/or harmful adverse drug reactions to drugs currently in routine use. We call a new suspected ADR a _signal_, and the practise of finding them _signal detection_.

A typical report of an adverse reaction, as stored in our database, contains a plethora of information about a suspected adverse event, and the patient that experienced it, all of which are carefully considered by expert signal assessors when trying to determine whether a potential signal is plausible and worth communicating to the global pharmacovigilance community.

However, since we have so many reports, with sometimes 100s of thousands of additional reports arriving to our database each week, these are far too many for expert assessors to read through and find patterns in manually. As such, signal detection turns to statistical and data mining methods in order to sift through the deluge of reports, and identify statistically suggestive patterns amongst the reports we receive.

There are a number of methods for looking for these patterns, but by far the most common methods fall under the umbrella of _disproportionality analysis_, which aims to identify reactions which are happening more frequently in combination with a certain drug, than would generally be expected from background rates alone.

In this blog post, I aim to describe each of the 4 most common methods of disproportionality analysis, and how they relate to one another;

* Reporting Odds Ratio
* Proportional Reporting Ratio
* Information component
* Empirical Bayes Geometric Mean

Naturally, there already exist a number of good resources for understanding these methods. I'll list the ones I used at the end of this post. However, I personally benefit from writing about methods to learn more about them, translating the classical statistics language into the language I am personally (as a recovering astrophysicist) more familiar with, and filling in the gaps in derivations and leaps in logic that I personally sometimes struggle with in the published literature. 

## The problem statement

On an adverse event report, alongside the information about a patient, a list of drugs that the patient took, and a list of reactions the patient experienced, each coded to their own respective standardised dictionaries. Disproportionality analysis applied to signal detection operates on a _combination_ of a drug and a reaction. There are then 4 possible things that can happen on an adverse event report;

* The report lists the drug **and** the reaction
* The report lists the drug **but not** the reaction
* The report lists the reaction **but not** the drug
* The report lists **neither** the drug **nor** the reaction

These scenarios are typically visualised in terms of a "contingency matrix", like so;

$$ 
\begin{array}{l|cc}
      & \textrm{DRUG} & \textrm{NOT DRUG} \\
    \hline
    \textrm{REACTION} & C_{xy} & C_{\overline{x}y} \\
    \textrm{NOT REACTION} & C_{x\overline{y}} & C_{\overline{x}\overline{y}}
\end{array}
$$

<!-- $$
\begin{array}{c|lcr}
n & \text{Left} & \text{Center} & \text{Right} \\
\hline
1 & 0.24 & 1 & 125 \\
2 & -1 & 189 & -8 \\
3 & -20 & 2000 & 1+10i
\end{array}
$$ -->



## Odds ratios

## Reporting Ratios

## Information Component (IC)

## Empirical Bayes Geometic Mean

## Bibliography


