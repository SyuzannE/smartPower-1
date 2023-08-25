# import matplotlib.pyplot as plt
# import numpy as np
#
#
# def analyse_data(df_home_consumption, df_solar_production):
#     # plot_multiple_kwh_day(all_days)
#
#     # consumption
#     calculate_totals(df_home_consumption, "power usage")
#
#     # solar
#     calculate_totals(df_solar_production, "solar production")
#
#
# def calculate_totals(data, type):
#     print(f"Avg Total {type}: {round(sum(data['avg']), 2)}")
#     total_all = [round(sum(values), 2) for values in data["all"]]
#     print(f"All days total {type}: {total_all}")
#     print(f"All days avg total {type}: {round(sum(total_all) / len(total_all), 2)}")
#
#
# def plot_kwh_day(data):
#     plt.style.use('_mpl-gallery')
#     x = np.linspace(0, 24, len(data))
#     y = data
#
#     # plot
#     fig, ax = plt.subplots()
#     ax.plot(x, y, linewidth=2.0)
#     ax.set(xlim=(0, 24), xticks=np.arange(1, 24),
#            ylim=(0, 3), yticks=np.arange(0, 4, 0.5))
#     plt.show()
#
#
# def plot_multiple_kwh_day(data):
#     plt.style.use('_mpl-gallery')
#     x = np.linspace(0, 24, len(data[0]))
#
#     # plot
#     fig, ax = plt.subplots(figsize=(10, 4), layout='constrained')
#     ax.plot(x, data[0], linewidth=2.0)
#     ax.plot(x, data[1], linewidth=2.0)
#     ax.plot(x, data[2], linewidth=2.0)
#     ax.plot(x, data[3], linewidth=2.0)
#     ax.set_xlabel('24H time')  # Add an x-label to the axes.
#     ax.set_ylabel('KwH')  # Add a y-label to the axes.
#     ax.set_title("Multiday KwH usage")
#     ax.set(xlim=(0, 24), xticks=np.arange(1, 24),
#            ylim=(0, 3), yticks=np.arange(0, 4, 0.5))
#     plt.show()
