#[derive(Debug)]
struct Tallerken {
    tid: i32,
    ris: i32,
    erter: i32,
    gulrøtter: i32,
    reinsdyrkjøtt: i32,
    sist_kjøtt_tid: i32,
    julekringle: i32,
}

impl Tallerken {
    fn new(ris: i32, erter: i32, gulrøtter: i32, reinsdyrkjøtt: i32, julekringle: i32) -> Self {
        Self {
            tid: 0,
            ris,
            erter,
            gulrøtter,
            reinsdyrkjøtt,
            sist_kjøtt_tid: 0,
            julekringle,
        }
    }
    fn runde(&mut self) {
        // Self::påfyll(self);
        Self::spise(self);
        self.tid += 1;
    }
    fn påfyll(&mut self) {
        self.ris += 1;
        self.erter += 1;

        if self.tid > 30 {
            self.gulrøtter += 1;
        }

        if self.reinsdyrkjøtt == 0 {
            self.reinsdyrkjøtt += 1;
        }
    }
    fn spise(&mut self) {
        if self.ris == 0 && self.erter == 0 && self.gulrøtter == 0 && self.reinsdyrkjøtt == 0 {
            self.julekringle -= 1
        }
        if self.ris != 0 && self.erter != 0 {
            self.ris -= 5;
            self.erter -= 3;
        } else if self.erter != 0 && self.gulrøtter != 0 {
            self.erter -= 5;
            self.gulrøtter -= 3;
        } else if self.gulrøtter != 0 && self.reinsdyrkjøtt != 0 {
            self.gulrøtter -= 5;
            self.reinsdyrkjøtt -= 3;
        }
    }
}

fn main() {
    let mut tallerken = Tallerken {
        tid: 0,
        ris: 100,
        erter: 100,
        gulrøtter: 100,
        reinsdyrkjøtt: 100,
        julekringle: 100,
    };

    dbg!(&tallerken);
    tallerken.runde();
    dbg!(tallerken);

    // let påfyll = [
    //     ("ris", [0, 0, 1, 0, 0, 2]),
    //     ("erter", [0, 3, 0, 0]),
    //     ("gulrøtter", [0, 1, 0, 0, 0, 8]),
    //     ("reinsdyrkjøtt", [100, 80, 40, 20, 10]),
    // ];
}
