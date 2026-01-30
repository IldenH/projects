/**
 * A Main class with a main function
 * @version 1.0
 * @author Me
 */
public class Main {
  public static void main(String[] args) {
    System.out.println("Hello world!"); // comment
    int oneMillion = 1_000_000;
    System.out.println(oneMillion);
    byte small = 72;
    System.out.println(small - 30);
    System.out.println(Math.PI - 3.2f);
    System.out.println(1.7e308);
    System.out.println("日本語上手");
    double money;
    long people;
    int days;
    boolean isRed;
    String exampleText;
    int へい = 3;
    System.out.println(へい);
    var myVar = true;
    var myInt = 67;
    final double SEK_TO_NOK = 1.06;
    System.out.println(NOK_TO_SEK);

    enum Size { SMALL, MEDIUM, LARGE, EXTRA_LARGE };
    Size s = Size.MEDIUM;

    System.out.println(Math.floorMod(12 + 3, 12));
    var safeMultiply = Math.multiplyExact(3, 3); // exception instead of wrapping around

    System.out.println(3 > 1 ? "hei" : "nei");
    int n = 7;
    int m = 7;
    int fourteen = 2 * n++;
    int sixteen = 2 * ++m;

    int seasonCode = 4;
    String season = switch (seasonCode) {
      case 0 -> "Spring";
      case 1 -> "Summer";
      case 2 -> "Fall";
      case 3 -> "Winter";
      default -> null;
    };
    System.out.println(season);
  }

  public static final double NOK_TO_SEK = 0.94;
}
