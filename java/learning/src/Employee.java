import java.text.NumberFormat;
import java.time.LocalDate;
import java.util.Objects;
import java.util.Random;

public class Employee {
  private static int nextId = 1;

  private int id;
  private String name;
  private double salary;
  private LocalDate hireDay;

  private static Random generator = new Random();

  static {
    nextId = generator.nextInt(10_000);
  }

  {
    id = nextId;
    nextId++;
  }

  public static void main(String[] args) {
    var staff = new Employee[4];
    staff[0] = new Employee();
    staff[1] = new Employee("Georg Green");
    staff[2] = new Employee();
    staff[3] = new Employee("Hell Maker", Math.PI, 2017, 4, 20);
    for (var e : staff) System.out.println(e.getInfo());
  }

  public Employee() {
    this("Employee #" + nextId);
  }

  public Employee(String n) {
    name = Objects.requireNonNullElse(n, "unknown");
    salary = 0;
    hireDay = LocalDate.now();
  }

  public Employee(String n, double s, int year, int month, int day) {
    // name = n;
    // name = Objects.requireNonNull(n, "Name can not be null")
    name = Objects.requireNonNullElse(n, "unknown");
    salary = s;
    hireDay = LocalDate.of(year, month, day);
  }

  public String getName() {
    return name;
  }

  public String getInfo() {
    NumberFormat nf = NumberFormat.getCurrencyInstance();
    return String.format("%s (id: %s) makes %s and was hired %s", name, id, nf.format(salary), hireDay);
  }
}
