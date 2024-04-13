import plotly.express as px
#from shared import app_dir, tips
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly, render_widget
import faicons as fa



#import dataset
tips = px.data.tips()
tips =tips.rename(columns={'size': 'size2'})

bill_rng = (min(tips.total_bill), max(tips.total_bill))
size_rng= (min(tips.size2), max(tips.size2))


# Add page title and sidebar
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_dark_mode(mode="dark"),
        ui.input_slider("total_bill", "Bill amount", min=bill_rng[0], max=bill_rng[1], value=bill_rng, pre="$",),
        ui.input_slider("size2", "Party Size", min=int(size_rng[0]), max=int(size_rng[1]), value=(size_rng)),
        ui.input_checkbox_group("time", "Food Service", ["Lunch", "Dinner"], selected=["Lunch", "Dinner"], inline=True), 
        ui.input_checkbox_group("day", "Day", ["Thur", "Fri", "Sat", "Sun"], selected=["Thur", "Fri", "Sat", "Sun"], inline=True),
        ui.input_action_button("reset", "Reset filter"),
        ui.h6("Links:"),
            ui.a(
            "GitHub Source",
            href="https://github.com/lauravos/cintel-06-custom",
            target="_blank",),  
        open="desktop",),
        
    ui.layout_columns(
        ui.value_box("Total tippers", ui.output_ui("total_tippers"), showcase=fa.icon_svg("user"), theme="bg-gradient-green-blue"),
        ui.value_box("Average tip", ui.output_ui("average_tip"), showcase=fa.icon_svg("percent"), theme="bg-gradient-green-blue"),
        ui.value_box("Average Tip Amount", ui.output_ui("average_tip2"), showcase=fa.icon_svg("money-bill-wave"), theme="bg-gradient-green-blue"),
        ui.value_box("Average bill", ui.output_ui("average_bill"), showcase=fa.icon_svg("receipt"), theme="bg-gradient-green-blue"),
        fill=False,),

    ui.layout_columns(
        #make data frame
        ui.card(
            ui.card_header("Tips Data"), 
            ui.output_data_frame("table"), 
            full_screen=True, 
        ),
        #make scatterplot
        ui.card(
            ui.card_header(
                "Bill Total vs Tip",
                ui.popover(
                    fa.icon_svg("ellipsis"),
                    ui.input_radio_buttons(
                        "scatter_color",
                        None,
                        ["none", "sex", "smoker", "day", "time"],
                        inline=True,
                    ),
                    title="Add a color variable",
                    placement="top",
                ),
                class_="d-flex justify-content-between align-items-center",
            ),
            output_widget("scatterplot"),
            full_screen=True,
        ),
       
        #make ridgeline plot
        ui.card(
            ui.card_header(
                "Tip Percentages",
                ui.popover(
                    fa.icon_svg("ellipsis"),
                    ui.input_radio_buttons(
                        "tip_perc_y",
                        "Split by:",
                        ["sex", "smoker", "day", "time"],
                        selected="day",
                        inline=True,),
                    title="Add a color variable",),
                class_="d-flex justify-content-between align-items-center",),
            output_widget("tip_perc"),
            full_screen=True,),
        col_widths=[6, 6, 12],),
    #ui.include_css(app_dir / "styles.css"),
    title="Gagnon-Vos Restaurant Tipping Project",
    fillable=True,)


def server(input, output, session):
    @reactive.calc
    def tips_data():
        bill = input.total_bill()
        psize = input.size2()
        idx1 = tips.total_bill.between(bill[0], bill[1])
        idx2 = tips.time.isin(input.time())
        idx3 = tips.day.isin(input.day())
        idx4 = tips.size2.between(psize[0], psize[1])
        return tips[idx1 & idx2 & idx3 & idx4]

    @render.ui
    def total_tippers():
        return tips_data().shape[0]

    @render.ui
    def average_tip():
        d = tips_data()
        if d.shape[0] > 0:
            perc = d.tip / d.total_bill
            return f"{perc.mean():.1%}"

    @render.ui
    def average_tip2():
        d = tips_data()
        if d.shape[0] > 0:
            perc = d.tip 
            return f"{perc.mean():.2f}" 

    @render.ui
    def average_bill():
        d = tips_data()
        if d.shape[0] > 0:
            bill = d.total_bill.mean()
            return f"${bill:.2f}"

    @render.data_frame
    def table():
        return render.DataGrid(tips_data())

    @render_plotly
    def scatterplot():
        color = input.scatter_color()
        return px.scatter(
            tips_data(),
            x="total_bill",
            y="tip",
            labels={"total_bill":"Bill($)", "tip":"Tip Amount($)"},
            color=None if color == "none" else color,
            trendline="lowess",
            trendline_color_override='indigo',)

    @render_plotly
    def tip_perc():
        from ridgeplot import ridgeplot

        dat = tips_data()
        dat["percent"] = dat.tip / dat.total_bill
        yvar = input.tip_perc_y()
        uvals = dat[yvar].unique()

        samples = [[dat.percent[dat[yvar] == val]] for val in uvals]

        plt = ridgeplot(
            samples=samples,
            labels=uvals,
            bandwidth=0.01,
            colorscale="plasma",
            colormode="row-index",)

        plt.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))

        return plt

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        ui.update_slider("total_bill", value=bill_rng)
        ui.update_slider("size2", value=size_rng)
        ui.update_checkbox_group("time", selected=["Lunch", "Dinner"])
        ui.update_checkbox_group("day", selected=["Thur", "Fri", "Sat", "Sun"])

app = App(app_ui, server)
