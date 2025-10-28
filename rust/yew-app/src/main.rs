use cached::proc_macro::cached;
use yew::prelude::*;

#[cached]
fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

enum Msg {
    AddOne,
}

struct App {
    value: u64,
}

impl Component for App {
    type Message = Msg;
    type Properties = ();

    fn create(_ctx: &Context<Self>) -> Self {
        Self { value: 1 }
    }

    fn update(&mut self, _ctx: &Context<Self>, msg: Self::Message) -> bool {
        match msg {
            Msg::AddOne => {
                self.value += 1;
                true
            }
        }
    }

    fn view(&self, ctx: &Context<Self>) -> Html {
        let start = 0;
        let end = 50;
        let fibbonacci = (start..end).map(|n| fibonacci(n)).map(|num| {
            html! {
                <p>{ num }</p>
            }
        });

        html! {
            <div>
                <button onclick={ctx.link().callback(|_| Msg::AddOne)}>{ "+1" }</button>
                <p>{ self.value }</p>
                <p>{ format!("Fibbonacci numbers n={start} to n={end}:") }</p>
                { for fibbonacci }
            </div>
        }
    }
}

fn main() {
    yew::Renderer::<App>::new().render();
}
