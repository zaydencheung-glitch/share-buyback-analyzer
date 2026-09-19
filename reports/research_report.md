# Share Buybacks and Diluted Share Count: A Ten-Company Study

## Abstract

This project examines whether corporate share buybacks are associated with lower diluted weighted-average share counts after the effects of share issuance and dilution. I analyzed ten companies from FY2022 through FY2025 by measuring year-over-year changes in diluted weighted-average shares, with the primary share data verified against SEC filings. Of the ten companies studied, six showed an overall net share reduction, three showed net dilution, and one remained essentially flat. The results suggest that buyback activity is often associated with lower diluted share counts, but the outcome is not automatic and varies significantly between companies.

## 1\. Introduction

When a company announces billions of dollars in share buybacks, it is easy to assume that its share count will fall by a similar amount. However, buybacks are only one side of the equation. Companies can also issue new shares through stock-based compensation and other forms of equity issuance, which can offset some or even all of the shares being repurchased. Because of this, I became interested in looking past the size of a company's announced buyback program and measuring what actually happened to its diluted share count.



I built this project to compare that outcome across ten large companies over the same four-year period. Instead of judging a buyback program based only on dollars spent, I tracked changes in diluted weighted-average shares from FY2022 through FY2025. This gave me a consistent way to see which companies experienced meaningful share-count reductions, which experienced dilution, and which remained relatively unchanged.

## 2\. Research Question

Are corporate share buybacks associated with lower diluted weighted-average share counts after the effects of share issuance and dilution?



I chose this question because the amount a company spends on buybacks does not necessarily show whether its diluted share count actually decreased. By measuring the year-over-year change in diluted weighted-average shares, I could focus on the net outcome after both share repurchases and new share issuance were reflected in the number.

## 3\. Why Share Buybacks Matter

Share buybacks are one way companies return capital to shareholders. By repurchasing shares, a company can reduce the number of shares among which its earnings and ownership are divided. However, that effect becomes less clear when the company is also issuing new shares. A company could spend billions of dollars on repurchases while its diluted share count decreases only slightly, stays flat, or even increases. This is why I focused on the net change in diluted shares rather than treating buyback spending itself as evidence of an effective reduction. The project does not attempt to determine whether buybacks are good or bad investments or whether companies bought their shares at favorable prices. Instead, it focuses on a narrower question that I could measure directly: after repurchases and dilution were reflected in the share count, did the number actually go down?

## 4\. Methodology

For this project, I used diluted weighted-average shares as my main variable and tracked how that figure changed from year to year. This allowed me to measure the net change in share count after both repurchases and new share issuance were reflected in the figure. My goal was not to prove that buybacks directly caused these changes, but to determine whether buyback activity was associated with an actual reduction in diluted share count.



I analyzed ten companies: Apple, Microsoft, Meta, Tesla, Palantir, Alphabet, Amazon, NVIDIA, JPMorgan Chase, and Costco. I used the same four-year period, FY2022 through FY2025, for every company so the comparisons would be consistent instead of simply using whichever four years were most recently available. This gave me four annual diluted-share observations for each company and three possible year-over-year comparisons: 2022–2023, 2023–2024, and 2024–2025. If two available observations were not from consecutive fiscal years, I did not treat them as a one-year comparison.



For each consecutive pair of fiscal years, I calculated Net Shares Retired by subtracting the current year's diluted weighted-average shares from the previous year's figure. I then divided that change by the previous year's diluted share count to calculate the Net Share Reduction Yield. A positive yield meant the company's diluted share count decreased, while a negative yield meant it increased. I classified changes within ±0.10% as Flat/Neutral so extremely small changes would not be treated as meaningful reductions or dilution. I also calculated each company's cumulative share-count change from FY2022 to FY2025 using the beginning and ending share counts rather than simply averaging the annual percentage changes.



I initially collected the financial data through the yfinance Python package, but I did not rely on the automated data alone. I checked the diluted weighted-average share figures for all ten companies from FY2022 through FY2025 against official SEC filings. When the automated data was missing or did not match the filing, I used the SEC figure instead. This was especially important for cases such as NVIDIA, where historical share figures had to be viewed on a split-adjusted basis. Repurchase spending and stock-based compensation were also collected when available, but I treated those as supporting variables rather than the main measurement because my analysis focuses on the actual net change in diluted shares.

## 5\. Data Sources

I used Yahoo Finance data retrieved through the yfinance Python package for my initial automated data collection. However, because Yahoo Finance is a secondary source, I verified the diluted weighted-average share figures used in my main calculations against official SEC filings. I checked all ten companies for FY2022 through FY2025 and used SEC figures when automated data was missing or needed correction. I also recorded the source and verification status of each observation in my dataset. Repurchase spending and stock-based compensation collected through yfinance were kept as supporting variables and were not verified to the same extent as the diluted share data.

## 6\. Calculations

I used two main calculations to measure changes in diluted share count. First, I calculated Net Shares Retired:

**Net Shares Retired = Previous Year Diluted Weighted-Average Shares − Current Year Diluted Weighted-Average Shares**

A positive result means the diluted share count decreased, while a negative result means the share count increased. I then calculated Net Share Reduction Yield:

**Net Share Reduction Yield (%) = (Net Shares Retired ÷ Previous Year Diluted Weighted-Average Shares) × 100**

Finally, I measured the total change across the full study period using:

Cumulative Share Count Change (%) = ((FY2025 Diluted Weighted-Average Shares − FY2022 Diluted Weighted-Average Shares) ÷ FY2022 Diluted Weighted-Average Shares) × 100

Unlike Net Share Reduction Yield, a negative cumulative change means the share count decreased, while a positive cumulative change means it increased.



For example, Apple’s diluted weighted-average share count decreased from 16.325819 billion shares in FY2022 to 15.812547 billion shares in FY2023. Using the formula, Apple had a net reduction of 513.272 million diluted shares during that comparison. Dividing 513.272 million by the FY2022 starting figure of 16.325819 billion gives a Net Share Reduction Yield of about 3.14%. This does not mean Apple literally repurchased exactly 513.272 million shares. Instead, it represents the net decrease in diluted weighted-average shares after repurchases and any offsetting share issuance or dilution were reflected in the final figure.

## 7\. Results

Across the ten companies in my study, the results were mixed, but reductions in diluted share count were more common than increases. From FY2022 through FY2025, six of the ten companies showed an overall net reduction in diluted weighted-average shares: Apple, Microsoft, Meta, Alphabet, NVIDIA, and JPMorgan Chase. Three companies—Tesla, Palantir, and Amazon—showed net dilution, meaning their diluted share counts increased over the same period. Costco was classified as Flat/Neutral, with almost no overall change. These results suggest that share buybacks were associated with lower diluted share counts for a majority of the companies studied, but this outcome was not consistent across every company.



The size of these changes also varied significantly between companies. Apple had a cumulative diluted share-count change of −8.09%, while Alphabet decreased by 7.06% and JPMorgan Chase decreased by 6.35%. Meta decreased by 4.74%, NVIDIA by 2.15%, and Microsoft by 0.99%. On the other side, Palantir had the largest increase in the study at 24.30%, followed by Amazon at 6.26% and Tesla at 1.53%. Costco changed by only 0.01%, which placed it within my Flat/Neutral threshold. This variation was important because simply labeling a company as a reduction or dilution did not show the magnitude of the change.

## 8\. Company Comparisons

Apple showed one of the clearest patterns of share-count reduction in the study. Its diluted weighted-average share count fell in all three year-over-year comparisons, resulting in a cumulative decline of 8.09% from FY2022 to FY2025. Its average annual Net Share Reduction Yield was 2.77%, meaning the reduction was not caused by just one unusually strong year. Apple is a useful example of a company where continued buyback activity occurred alongside a consistent decline in diluted share count. However, the analysis still cannot conclude that buybacks alone caused the decline because diluted share count reflects the combined effects of repurchases and share issuance.



Palantir showed almost the opposite pattern. Its diluted weighted-average share count increased in all three year-over-year comparisons, producing a 24.30% cumulative increase from FY2022 to FY2025, the largest increase among the ten companies studied. Its average annual Net Share Reduction Yield was −7.56%, meaning dilution consistently outweighed any reduction in diluted shares over the period. Palantir demonstrates why looking only at repurchase activity does not provide a complete picture of what happened to diluted share count. The more important question for this project is what happened to diluted share count after all forms of issuance and reduction were reflected in the final number.



Costco represents the middle ground between the two. Its diluted weighted-average share count changed by only 0.01% from FY2022 to FY2025, making its overall share count essentially unchanged during the study period. Because I classified changes within ±0.10% as Flat/Neutral, Costco was not labeled as either a meaningful reduction or dilution. This case shows why I included a neutral category. Without it, an extremely small change could technically be labeled as a reduction or increase even though the difference was not meaningful for this analysis.

## 9\. Interpretation

The results suggest that share buybacks are often associated with a reduction in diluted share count, but that relationship is not automatic. Six of the ten companies in my study ended FY2025 with fewer diluted weighted-average shares than they had in FY2022, while three ended with more and one remained essentially unchanged. What stood out to me was how different the outcomes could be even though these companies all operate at a large scale. This reinforces the main reason I built the analyzer: the amount spent on buybacks does not tell the whole story. Looking at the change in diluted shares provides another way to see whether a company's share count actually decreased after dilution and issuance were taken into account.



Repurchase spending and stock-based compensation helped provide context for these results, but I did not treat either one as a direct explanation for changes in share count. Stock-based compensation can contribute to dilution, but it is not the only way new shares can enter the calculation, and the dollar value of compensation cannot simply be subtracted from the dollar value of buybacks. Because of this, I treated these figures as supporting information rather than using them to calculate a supposed “net buyback” amount. This kept the analysis focused on what I could directly measure: whether diluted weighted-average shares ultimately increased or decreased.

## 10\. Limitations

There are several limitations to this analysis. First, diluted weighted-average shares are an accounting measure averaged across a reporting period, not a literal count of shares outstanding on the final day of the fiscal year. A decrease in this figure also does not prove that buybacks created value for shareholders, since this project does not consider the price companies paid for their shares or whether those shares were undervalued or overvalued. Changes in diluted weighted-average shares can also reflect several factors besides buybacks, including stock-based compensation and other forms of share issuance. In addition, the four-year period from FY2022 through FY2025 provides a consistent comparison across companies but is still a relatively short period. Fiscal-year dates also differ between companies, meaning the periods are not perfectly identical in calendar time.



Another limitation is the data itself. I verified the diluted weighted-average share figures used in the main analysis against SEC filings, but supporting variables such as repurchase spending and stock-based compensation were primarily collected through yfinance and were not fully verified in the same way. Automated financial data can also use different accounting labels or presentations than company filings. Finally, this study identifies an association, not causation. The results can show that buyback activity and a lower diluted share count occurred together, but they cannot prove that buybacks alone caused the change.

## 11\. Conclusion

Across the ten companies and four fiscal years I studied, six companies showed an overall reduction in diluted weighted-average shares, three showed net dilution, and one remained essentially flat. These results answer my original question with an important qualification: share buybacks were associated with lower diluted share counts for a majority of the companies in my sample, but that outcome was not guaranteed. Companies such as Apple consistently reduced their diluted share counts, while others, especially Palantir, experienced substantial dilution over the same period.

The biggest takeaway from this project is that buyback spending alone does not show what ultimately happened to shareholders' diluted ownership. Looking at the net change in diluted shares accounts for the fact that companies can repurchase shares while simultaneously issuing new ones. At the same time, a lower share count does not necessarily mean a buyback program created shareholder value. My analysis measures one specific outcome—the change in diluted weighted-average shares—and provides a way to evaluate that outcome consistently across companies.

## 12\. Sources

* Automated Data: Yahoo Finance, accessed through the yfinance Python package.
Used for initial automated data collection and supporting financial variables.
* Apple Inc. — Forms 10-K for the fiscal years ended September 24, 2022 (SEC Accession No. 0000320193-22-000108) and September 27, 2025 (SEC Accession No. 0000320193-25-000079). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Microsoft Corporation — Forms 10-K for the fiscal years ended June 30, 2023 (SEC Accession No. 0000950170-23-035122) and June 30, 2025 (SEC Accession No. 0000950170-25-100235). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Meta Platforms, Inc. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0001326801-25-000017) and December 31, 2025 (SEC Accession No. 0001628280-26-003942). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Tesla, Inc. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0001628280-25-003063) and December 31, 2025 (SEC Accession No. 0001628280-26-003952). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Palantir Technologies Inc. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0001321655-25-000022) and December 31, 2025 (SEC Accession No. 0001321655-26-000011). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Alphabet Inc. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0001652044-25-000014) and December 31, 2025 (SEC Accession No. 0001652044-26-000018). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Amazon.com, Inc. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0001018724-25-000004) and December 31, 2025 (SEC Accession No. 0001018724-26-000004). Used to verify diluted weighted-average shares for FY2022–FY2025.
* NVIDIA Corporation — Forms 10-K for the fiscal years ended January 30, 2022 (SEC Accession No. 0001045810-22-000036) and January 26, 2025 (SEC Accession No. 0001045810-25-000023). Used to verify diluted weighted-average shares. NVIDIA's FY2022 share figure was adjusted to a comparable basis for the company's 2024 10-for-1 stock split.
* JPMorgan Chase \& Co. — Forms 10-K for the fiscal years ended December 31, 2024 (SEC Accession No. 0000019617-25-000270) and December 31, 2025 (SEC Accession No. 0001628280-26-008131). Used to verify diluted weighted-average shares for FY2022–FY2025.
* Costco Wholesale Corporation — Forms 10-K for the fiscal years ended September 1, 2024 (SEC Accession No. 0000909832-24-000049) and August 31, 2025 (SEC Accession No. 0000909832-25-000101). Used to verify diluted weighted-average shares for FY2022–FY2025.
* All SEC filings were accessed through the U.S. Securities and Exchange Commission's EDGAR database. Supporting variables retrieved through yfinance, including repurchase spending and stock-based compensation, were used as contextual information and were not verified to the same extent as the diluted weighted-average share figures.

